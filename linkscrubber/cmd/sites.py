import logging
import urlparse

from cliff import lister

LOG = logging.getLogger(__name__)


class Sites(lister.Lister):
    """List the unique sites in the bookmarks.
    """

    def take_action(self, parsed_args):
        client = self.app.get_client()
        LOG.info('downloading bookmarks')
        bookmarks = client.posts()
        LOG.info('have %d bookmarks', len(bookmarks))
        sites = set()
        for bm in bookmarks:
            parsed_url = urlparse.urlparse(bm['href'])
            sites.add(parsed_url.netloc)
        return (('Site',),
                # Need to return tuples for the formatting code,
                # so wrap the strings.
                ((s,) for s in sorted(sites)))
