"""Main program for linkscrubber
"""

import argparse
import getpass
import logging
import Queue
import sys
import threading
import urlparse

import pinboard
import pkg_resources
import requests

LOG = None


def _get_argument_parser():
    """Create the argparse parser for the program.
    """
    dist = pkg_resources.get_distribution('linkscrubber')

    parser = argparse.ArgumentParser(
        description="pinboard.in link cleaner",
        version=dist.version,
    )

    auth_group = parser.add_argument_group('authentication')
    identity = auth_group.add_mutually_exclusive_group()

    identity.add_argument(
        '--user', '-u',
        help="pinboard.in username",
    )
    identity.add_argument(
        '--token', '-t',
        help='pinboard.in API token',
    )

    auth_group.add_argument(
        '--password', '-p',
        help="pinboard.in password",
    )

    behavior_group = parser.add_argument_group('behavior')
    behavior_group.add_argument(
        '--dry-run', '-n',
        dest='dry_run',
        default=False,
        action='store_true',
        help='show the changes, but do not make them',
    )
    behavior_group.add_argument(
        '--redirect-site',
        dest='redirect_sites',
        action='append',
        default=['feedproxy.google.com'],
        help='replace redirects originating from these sites',
    )
    behavior_group.add_argument(
        '--all-redirects',
        dest='all_redirects',
        action='store_true',
        default=False,
        help='replace all links that cause a redirect',
    )
    behavior_group.add_argument(
        '-N', '--num-workers',
        dest='num_workers',
        action='store',
        type=int,
        default=4,
        help='how many bookmarks to check at one time',
    )

    output_group = parser.add_argument_group('output')
    output_group.add_argument(
        '-V', '--verbose',
        dest='verbosity',
        action='append_const',
        const=1,
        default=[1],
        help='repeat for more detailed output',
    )
    output_group.add_argument(
        '-q', '--quiet',
        dest='verbosity',
        action='store_const',
        const=[],
        help='turn off output',
    )
    return parser


def _configure_logging(verbosity):
    """Set up the logging module for messages
    going to stdout, including the global
    LOG variable used in this module.
    """
    global LOG

    # Set up output
    log_levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    log_level = log_levels.get(verbosity, logging.DEBUG)

    logging.basicConfig(
        level=log_level,
        format='%(message)s',
    )

    if verbosity > 2:
        logging.getLogger('requests').setLevel(logging.DEBUG)
    else:
        logging.getLogger('requests').setLevel(logging.WARNING)

    LOG = logging.getLogger(__name__)


def _get_client(username, password, token):
    """Create a pinboard client with the provided credentials.
    """
    # Make sure we have a password
    if username and not password:
        password = getpass.getpass()

    # Get a pinboard client
    if token:
        LOG.debug('logging in with token')
    else:
        LOG.debug('logging in with username and password')

    client = pinboard.open(
        username,
        password,
        token,
    )
    return client


def _get_bookmarks(client, bookmark_queue, check_all, sites):
    """Use the client to find the dates when bookmarks were added, query
    for the bookmarks for that date, and put them in the bookmarks
    queue.
    """
    sites = set(sites)
    dates = client.dates()
    LOG.info('processing %d dates', len(dates))
    for d in dates:
        LOG.info('looking at posts from %s', d['date'])
        try:
            bookmarks = client.posts(date=d['date'])
        except Exception as err:
            LOG.error('Could not retrieve posts from %s: %s', d['date'], err)
        kept = 0
        for bm in bookmarks:
            if check_all:
                keep = True
            else:
                parsed_url = urlparse.urlparse(bm['href'])
                keep = parsed_url.netloc in sites
            if keep:
                LOG.info('processing %s (%s)', bm['href'], bm['description'])
                bookmark_queue.put(bm)
                kept += 1
        if kept:
            LOG.info('found %s posts to process from %s', kept, d['date'])


def _check_bookmarks_worker(bookmark_queue, update_queue):
    LOG.debug('starting bookmark worker')
    while True:
        bm = bookmark_queue.get()
        if not bm:
            break
        LOG.debug('examining %s (%s)', bm['href'], bm['description'])
        try:
            response = requests.head(bm['href'])
        except Exception as err:
            LOG.error('Could not retrieve %s (%s): %s' %
                      (bm['href'], bm['description'], err))
        if response.status_code / 100 == 3:
            # 3xx status means a redirect
            try:
                update_queue.put((bm, response.headers['location']))
            except KeyError:
                # No new location for the redirect?
                LOG.error('redirect for %s (%s) did not include location',
                          bm['href'], bm['description'])
        bookmark_queue.task_done()


def _update_worker(client, update_queue):
    """Pull update items out of the queue and make the changes on pinboard.
    """
    LOG.debug('starting update worker')
    num_updates = 0
    while True:
        update = update_queue.get()
        if not update:
            break
        bm, new_url = update
        LOG.info('changing %s to %s', bm['href'], new_url)
        try:
            client.add(
                url=new_url,
                description=bm['description'],
                extended=bm['extended'],
                tags=bm['tags'],
                date=bm['time_parsed'][:3],
            )
        except Exception as err:
            LOG.error('Failed to create new post for %s: %s', new_url, err)
        else:
            client.delete(bm['href'])
    LOG.info('Updated %d bookmarks', num_updates)


def _dry_run_worker(update_queue):
    """Show the updates that would be made.
    Used in --dry-run mode.
    """
    LOG.debug('starting dry-run worker')
    while True:
        update = update_queue.get()
        if not update:
            break
        bm, new_url = update
        LOG.info('DRY RUN changing %s to %s', bm['href'], new_url)


def main(argv=sys.argv[1:]):
    parser = _get_argument_parser()
    arguments = parser.parse_args(argv)

    _configure_logging(len(arguments.verbosity))

    date_client = _get_client(
        arguments.user,
        arguments.password,
        arguments.token,
    )

    # Queue to hold the bookmarks to be processed
    bookmark_queue = Queue.Queue()

    # Queue to hold the bookmarks to be updated
    update_queue = Queue.Queue()

    check_bookmarks_threads = [
        threading.Thread(
            target=_check_bookmarks_worker,
            args=(bookmark_queue, update_queue),
            name='check-bookmarks-%d' % i,
        )
        for i in range(arguments.num_workers)
    ]

    if arguments.dry_run:
        update_thread = threading.Thread(
            target=_dry_run_worker,
            args=(update_queue,),
            name='update-thread',
        )
    else:
        # I don't know if the pinboard client is thread-safe, so make
        # another one to use for the update worker.
        update_client = _get_client(
            arguments.user,
            arguments.password,
            arguments.token,
        )
        update_thread = threading.Thread(
            target=_update_worker,
            args=(update_client, update_queue),
            name='update-thread',
        )
    update_thread.setDaemon(True)

    # Start all of the workers
    update_thread.start()
    for t in check_bookmarks_threads:
        t.setDaemon(True)
        t.start()

    # Get the bookmarks that need to be processed
    _get_bookmarks(
        date_client,
        bookmark_queue,
        arguments.all_redirects,
        arguments.redirect_sites,
    )
    # Sent poison pills to the workers to make them exit when they are
    # done processing the real data
    for t in check_bookmarks_threads:
        LOG.debug('telling %s to stop', t.name)
        bookmark_queue.put(None)
    for t in check_bookmarks_threads:
        LOG.debug('waiting for %s', t.name)
        t.join()
    update_queue.put(None)
    LOG.debug('waiting for %s', update_thread.name)
    update_thread.join()

    return 0
