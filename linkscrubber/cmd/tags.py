import logging

from cliff import command


class TagsCanonicalize(command.Command):
    """Combine tags that are the same except for capitalization.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        import pinboard
        pinboard._debug = 1
        client = self.app.get_client()

        all_tags = client.tags()
        self.log.info('Found %d separate tags', len(all_tags))

        tag_names = (t['name'] for t in all_tags)
        for tag in tag_names:
            c_tag = tag.lower()
            if c_tag != tag:
                temp_tag = c_tag + '-renaming'
                self.log.info('Rename "%s" to "%s"', tag, c_tag)
                if not self.app.options.dry_run:
                    client.rename_tag(tag, temp_tag)
                    client.rename_tag(temp_tag, c_tag)


class TagRename(command.Command):
    """Rename a tag or combine it with another tag.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(TagRename, self).get_parser(prog_name)
        parser.add_argument(
            'original',
            help='original tag name',
        )
        parser.add_argument(
            'new',
            help='new tag name',
        )
        return parser

    def take_action(self, parsed_args):
        import pinboard
        pinboard._debug = 1
        client = self.app.get_client()

        self.log.info('Renaming tag %s to %s',
                      parsed_args.original, parsed_args.new)

        if not self.app.options.dry_run:
            client.rename_tag(parsed_args.original, parsed_args.new)
