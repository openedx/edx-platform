"""
Utilities for Open edX unit tests.
"""
from __future__ import absolute_import, unicode_literals

import django


# TODO: Remove Django 1.11 upgrade shim
# SHIM: We should be able to get rid of this utility post-upgrade
def expected_redirect_url(relative_url, hostname='testserver'):
    """
    Get the expected redirect URL for the current Django version and the
    given relative URL.  Django 1.8 and earlier redirect to absolute URLs,
    later versions redirect to relative ones.
    """
    if django.VERSION < (1, 9):
        return 'http://{}{}'.format(hostname, relative_url)
    else:
        return relative_url
