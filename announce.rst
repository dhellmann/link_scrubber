=====================================================
 Link Scrubber 1.0 -- a pinboard.in bookmark cleaner
=====================================================

.. tags:: python linkscrubber release

With the `announcement that Google Reader is being shuttered`_, I
decided I needed to go through my `pinboard.in`_ bookmarks and update
any that point to a ``feedproxy.google.com`` URL while their
redirecting service is still online. This script does that
automatically.

.. _announcement that Google Reader is being shuttered: http://googleblog.blogspot.com/2013/03/a-second-spring-of-cleaning.html
.. _pinboard.in: http://pinboard.in

What does it do?
================

``link_scrubber`` processes all of your bookmarks, looking for those
that redirect. It adds a new bookmark with the target of the redirect
and all the same metadata from the original link. By default, only
URLs from ``feedproxy.google.com`` are processed, but there are
command line options to process all redirects or to add more
individual sites.

The links are processed in small batches to reduce the load of
individual calls against the pinboard API server, so it can take a
while to process. Once a batch of links is fetched, it is checked in
parallel to speed things up a little.

Using
=====

See `the README`_ for details on installing and running.

.. _the README: https://pypi.python.org/pypi/linkscrubber

Disclaimer
==========

You should back up your account before running the script. I have done
some testing, but only against one account. Yours might behave
differently.

Reporting Bugs
==============

Use the github bug tracker at
https://github.com/dhellmann/link_scrubber to report problems.
