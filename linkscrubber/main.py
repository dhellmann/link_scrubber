"""Main program for linkscrubber
"""

import argparse
import getpass
import logging
import sys

import pinboard
import pkg_resources
from linkscrubber import processing

LOG = None


def _get_argument_parser():
    """Create the argparse parser for the program.
    """
    dist = pkg_resources.get_distribution('linkscrubber')

    parser = argparse.ArgumentParser(
        description="pinboard.in link cleaner",
    )

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + dist.version)

    auth_group = parser.add_argument_group(
        'authentication',
        'provide either a token or a username and password',
    )
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

    behavior_group = parser.add_argument_group(
        'behavior',
        'general behavioral controls',
    )
    behavior_group.add_argument(
        '--add-only', '-A',
        dest='add_only',
        default=False,
        action='store_true',
        help='add new copies of the links but do not delete any data',
    )
    behavior_group.add_argument(
        '--redirect-site',
        dest='redirect_sites',
        action='append',
        default=['feedproxy.google.com'],
        help=('replace redirects originating from these sites, '
              'defaults to [feedproxy.google.com], repeat the '
              'option to add sites'),
    )
    behavior_group.add_argument(
        '--all-redirects',
        dest='all_redirects',
        action='store_true',
        default=False,
        help=('replace all links that cause a redirect, '
              'not just the --redirect-sites values'),
    )

    stop_group = parser.add_argument_group(
        'stopping',
        'options to control when to end processing',
    )
    stop_group.add_argument(
        '--dry-run', '-n',
        dest='dry_run',
        default=False,
        action='store_true',
        help='show the changes, but do not make them',
    )
    stop_group.add_argument(
        '--stop-early',
        dest='stop_early',
        action='store_true',
        default=False,
        help=('stop processing on the '
              'first day without any redirecting links'),
    )
    stop_group.add_argument(
        '--no-stop-early',
        dest='stop_early',
        action='store_false',
        help=('process all posts, '
              'not just up to the first day without a redirect link'),
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
        format='%(threadName)s:%(message)s',
    )

    if verbosity > 2:
        logging.getLogger('requests').setLevel(logging.DEBUG)
        pinboard._debug = True
    else:
        logging.getLogger('requests').setLevel(logging.WARNING)

    LOG = logging.getLogger(__name__)


def main(argv=sys.argv[1:]):
    parser = _get_argument_parser()
    arguments = parser.parse_args(argv)

    # Make sure we have a password
    if arguments.user and not arguments.password:
        arguments.password = getpass.getpass()

    _configure_logging(len(arguments.verbosity))

    processing.process_bookmarks(
        (arguments.user, arguments.password, arguments.token),
        arguments.dry_run,
        arguments.add_only,
        arguments.stop_early,
        arguments.all_redirects,
        arguments.redirect_sites,
    )

    return 0
