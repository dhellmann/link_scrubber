import logging
from six.moves import queue
import re
import threading
try:
    # Python 2
    import urlparse
except:
    # Python 3
    import urllib.parse as urlparse

from cliff import command
import requests

# The number of threads to use for checking links. The user probably
# doesn't need to control this.
NUM_WORKERS = 4

LOG = logging.getLogger(__name__)


class Redirects(command.Command):
    "Replace redirects with the destination link."

    log = LOG

    def get_parser(self, prog_name):
        parser = super(Redirects, self).get_parser(prog_name)
        parser.add_argument(
            '--add-only', '-A',
            dest='add_only',
            default=False,
            action='store_true',
            help='add new copies of the links but do not delete any data',
        )
        parser.add_argument(
            '--redirect-site',
            dest='redirect_sites',
            action='append',
            default=['feedproxy.google.com'],
            help=('replace redirects originating from these sites, '
                  'defaults to [feedproxy.google.com], repeat the '
                  'option to add sites'),
        )
        parser.add_argument(
            '--redirect-site-regex',
            dest='redirect_regexes',
            action='append',
            default=[
                '^feeds?\.',
                '\.feedsportal\.com',
                't\.co',
                '.*\.ly$',
                'lnkd\.in',
                'red\.ht',
                'nyti\.ms',
            ],
            help=('pattern to match against site name to '
                  'check for redirects, defaults to '
                  '["^feeds?\.", "\.feedsportal\.com"], '
                  'repeat the option to add patterns'),
        )
        parser.add_argument(
            '--all-redirects',
            dest='all_redirects',
            action='store_true',
            default=False,
            help=('replace all links that cause a redirect, '
                  'not just the --redirect-sites values'),
        )
        return parser

    def take_action(self, parsed_args):
        date_client = self.app.get_client()

        # Queue to hold the bookmarks to be processed
        bookmark_queue = queue.Queue()

        # Queue to hold the bookmarks to be updated
        update_queue = queue.Queue()

        check_bookmarks_threads = [
            threading.Thread(
                target=_check_bookmarks_worker,
                args=(bookmark_queue, update_queue),
                name='check-bookmarks-%d' % i,
            )
            for i in range(NUM_WORKERS)
        ]

        if self.app.options.dry_run:
            update_thread = threading.Thread(
                target=_dry_run_worker,
                args=(update_queue,),
                name='update-thread',
            )
        else:
            # I don't know if the pinboard client is thread-safe, so make
            # another one to use for the update worker.
            update_client = self.app.get_client()
            update_thread = threading.Thread(
                target=_update_worker,
                args=(update_client, update_queue, parsed_args.add_only),
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
            parsed_args.all_redirects,
            parsed_args.redirect_sites,
            [re.compile(r) for r in parsed_args.redirect_regexes],
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


def _get_bookmarks(client, bookmark_queue, check_all, sites, regexes):
    """Use the client to find the dates when bookmarks were added, query
    for the bookmarks for that date, and put them in the bookmarks
    queue.
    """
    LOG.info('downloading bookmarks')
    bookmarks = client.posts()
    LOG.info('have %d bookmarks', len(bookmarks))
    kept = 0
    for bm in bookmarks:
        if check_all:
            keep = True
        else:
            parsed_url = urlparse.urlparse(bm['href'])
            keep = (
                parsed_url.netloc in sites
                or
                any(r.match(parsed_url.netloc) for r in regexes)
            )
        if keep:
            LOG.info('adding %s to processing queue (%s)',
                     bm['href'], bm['description'])
            bookmark_queue.put(bm)
            kept += 1
    if kept:
        LOG.info('found %s posts to process', kept)


def _check_bookmarks_worker(bookmark_queue, update_queue):
    LOG.debug('starting bookmark worker')
    while True:
        bm = bookmark_queue.get()
        if not bm:
            break
        LOG.debug('examining %s (%s)', bm['href'], bm['description'])
        try:
            response = requests.head(bm['href'])
            LOG.debug('response status: %s', response.status_code)
        except Exception as err:
            LOG.error('Could not retrieve %s (%s): %s' %
                      (bm['href'], bm['description'], err))
        if response.status_code // 100 == 3:
            # 3xx status means a redirect
            try:
                LOG.debug('preparing to update %s' % bm['href'])
                update_queue.put((bm, response.headers['location']))
            except KeyError:
                # No new location for the redirect?
                LOG.error('redirect for %s (%s) did not include location',
                          bm['href'], bm['description'])
        else:
            LOG.debug('no redirect for %s (%s)', bm['href'], bm['description'])
        bookmark_queue.task_done()


def _update_worker(client, update_queue, add_only):
    """Pull update items out of the queue and make the changes on pinboard.
    """
    LOG.debug('starting update worker')
    num_updates = 0
    while True:
        update = update_queue.get()
        if not update:
            break
        bm, new_url = update
        if add_only:
            LOG.info('adding %s', new_url)
        else:
            LOG.info('changing %s to %s (%s)',
                     bm['href'], new_url, bm['description'])
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
            LOG.debug('added %s', new_url)
            if not add_only:
                LOG.debug('deleting old post %s', bm['href'])
                try:
                    client.delete(bm['href'])
                except Exception as err:
                    LOG.error('Failed to remove old post for %s: %s',
                              bm['href'], err)
                else:
                    LOG.debug('deleted %s', bm['href'])
        num_updates += 1
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
