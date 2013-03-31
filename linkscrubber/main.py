"""Main program for linkscrubber
"""

import argparse
import getpass
import logging
import sys

import pkg_resources

import pinboard

LOG = None


def _get_argument_parser():
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
        help='Show the changes, but do not make them',
    )
    behavior_group.add_argument(
        '--redirect-site',
        dest='redirect_sites',
        action='append',
        default=['feedproxy.google.com'],
        help='Replace redirects originating from these sites',
    )
    behavior_group.add_argument(
        '--all-redirects',
        dest='all_redirects',
        action='store_true',
        default=False,
        help='Replace all links that cause a redirect',
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

    LOG = logging.getLogger(__name__)


def _get_client(username, password, token):
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


def main(argv=sys.argv[1:]):
    parser = _get_argument_parser()
    arguments = parser.parse_args(argv)

    _configure_logging(len(arguments.verbosity))

    client = _get_client(
        arguments.user,
        arguments.password,
        arguments.token,
    )

    d = client.dates()
    print len(d)

    return 0
