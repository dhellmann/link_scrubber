from linkscrubber import processing

import mock


def test_replace():
    responses = iter([
        ({
            'href': 'http://example.com/blah',
            'description': 'example link',
            'extended': 'extended',
            'tags': ['tag1', 'tag2'],
            'time_parsed': (2013, 3, 31, 9, 9, 9)},
         'http://newlink.com/blah'),
        None,
    ])
    q = mock.Mock()
    q.get = lambda *x, **k: next(responses)

    client = mock.Mock()

    processing._update_worker(client, q, False)

    client.add.assert_called_with(
        url='http://newlink.com/blah',
        description='example link',
        extended='extended',
        tags=['tag1', 'tag2'],
        date=(2013, 3, 31),
    )
    client.delete.assert_called_with(
        'http://example.com/blah',
    )


def test_add_only():
    responses = iter([
        ({
            'href': 'http://example.com/blah',
            'description': 'example link',
            'extended': 'extended',
            'tags': ['tag1', 'tag2'],
            'time_parsed': (2013, 3, 31, 9, 9, 9)},
         'http://newlink.com/blah'),
        None,
    ])
    q = mock.Mock()
    q.get = lambda *x, **k: next(responses)

    client = mock.Mock()
    client.delete.side_effect = AssertionError('should not delete')

    processing._update_worker(client, q, True)

    client.add.assert_called_with(
        url='http://newlink.com/blah',
        description='example link',
        extended='extended',
        tags=['tag1', 'tag2'],
        date=(2013, 3, 31),
    )
