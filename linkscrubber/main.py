"""Main program for linkscrubber
"""

import getpass
import logging
import sys

from cliff import app
from cliff import commandmanager
import pinboard
import pkg_resources
from linkscrubber import processing

LOG = None


class LinkScrubber(app.App):

    def __init__(self):
        version = pkg_resources.get_distribution('linkscrubber').version
        super(LinkScrubber, self).__init__(
            description='pinboard.in cleanup app',
            version=version,
            command_manager=commandmanager.CommandManager('linkscrubber'),
        )

    def build_option_parser(self, description, version, argparse_kwargs=None):
        parser = super(LinkScrubber, self).build_option_parser(
            description, version, argparse_kwargs,
        )

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

        parser.add_argument(
            '--dry-run', '-n',
            dest='dry_run',
            default=False,
            action='store_true',
            help='show the changes, but do not make them',
        )
        return parser

    @property
    def auth_args(self):
        return (self.options.user, self.options.password, self.options.token)

    def initialize_app(self, argv):
        # Make sure we have a password
        if self.options.user and not self.options.password:
            self.options.password = getpass.getpass()
        return


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
    app = LinkScrubber()
    return app.run(argv)
