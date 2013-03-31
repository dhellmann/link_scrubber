from linkscrubber import processing

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
    processing._get_bookmarks(
        client,
        q,
        stop_early=False,
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
    processing._get_bookmarks(
        client,
        q,
        stop_early=False,
        check_all=False,
        sites=['example.com'],
    )
    q.put.assert_called_with(
        {'href': 'http://example.com/blah',
         'description': 'example link'}
    )


def test_stop_early():
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
    processing._get_bookmarks(
        client,
        q,
        stop_early=True,
        check_all=False,
        sites=['feedproxy.google.com'],
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
    processing._get_bookmarks(
        client,
        q,
        stop_early=True,
        check_all=True,
        sites=['feedproxy.google.com'],
    )
    q.put.assert_called_with(
        {'href': 'http://example.com/blah',
         'description': 'example link'}
    )
