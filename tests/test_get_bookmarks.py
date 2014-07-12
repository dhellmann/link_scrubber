from linkscrubber.cmd import redirects

import mock


def test_no_site_match():
    client = mock.Mock()
    client.dates.return_value = [
        {'date': 'ignored'},
    ]
    client.posts.return_value = [
        {'href': 'http://example.com/blah',
         'description': 'example link'},
    ]
    q = mock.Mock()
    q.put.side_effect = AssertionError('should not have called put')
    redirects._get_bookmarks(
        client,
        q,
        check_all=False,
        sites=['feedproxy.google.com'],
    )


def test_site_match():
    client = mock.Mock()
    client.dates.return_value = [
        {'date': 'ignored'},
    ]
    client.posts.return_value = [
        {'href': 'http://example.com/blah',
         'description': 'example link'},
    ]
    q = mock.Mock()
    redirects._get_bookmarks(
        client,
        q,
        check_all=False,
        sites=['example.com'],
    )
    q.put.assert_called_with(
        {'href': 'http://example.com/blah',
         'description': 'example link'}
    )


def test_check_all():
    client = mock.Mock()
    client.dates.return_value = [
        {'date': 'ignored'},
    ]
    client.posts.return_value = [
        {'href': 'http://example.com/blah',
         'description': 'example link'},
    ]
    q = mock.Mock()
    redirects._get_bookmarks(
        client,
        q,
        check_all=True,
        sites=['feedproxy.google.com'],
    )
    q.put.assert_called_with(
        {'href': 'http://example.com/blah',
         'description': 'example link'}
    )
