import logging

from cliff import command


class TagsCanonicalize(command.Command):
    """Combine tags that are the same except for capitalization.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        client = self.app.get_client()

        all_tags = client.tags()
        self.log.info('Found %d separate tags', len(all_tags))

        tag_names = (t['name'] for t in all_tags)
        for tag in tag_names:
            c_tag = tag.lower()
            if c_tag != tag:
                self.log.info('Rename "%s" to "%s"', tag, c_tag)
                if not self.app.options.dry_run:
                    client.rename_tag(tag, c_tag)
