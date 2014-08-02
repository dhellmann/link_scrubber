"""Main program for linkscrubber
"""

import getpass
import logging
import sys

from cliff import app
from cliff import commandmanager
import pinboard
import pkg_resources


class LinkScrubber(app.App):

    log = logging.getLogger(__name__)

    def __init__(self):
        version = pkg_resources.get_distribution('linkscrubber').version
        super(LinkScrubber, self).__init__(
            description='pinboard.in cleanup app',
            version=version,
            command_manager=commandmanager.CommandManager('linkscrubber'),
        )

    def configure_logging(self):
        super(LinkScrubber, self).configure_logging()
        if self.options.verbose_level > 2:
            logging.getLogger('requests').setLevel(logging.DEBUG)
            pinboard._debug = True
        else:
            logging.getLogger('requests').setLevel(logging.WARNING)

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

    def get_client(self):
        """Create a pinboard client.
        """
        # Get a pinboard client
        if self.options.token:
            self.log.debug('logging in with token')
        else:
            self.log.debug('logging in with username and password')

        client = pinboard.open(
            self.options.user,
            self.options.password,
            self.options.token,
        )
        return client

    def initialize_app(self, argv):
        # Make sure we have a password
        if self.options.user and not self.options.password:
            self.options.password = getpass.getpass()
        return


def main(argv=sys.argv[1:]):
    app = LinkScrubber()
    return app.run(argv)
