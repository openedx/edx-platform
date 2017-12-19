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
    given relative URL:

    * Django 1.8 and earlier redirect URLs beginning with a slash to absolute
      URLs, later versions redirect to relative ones.
    * Django 1.8 and earlier leave URLs without a leading slash alone, later
      versions prepend the missing slash.
    """
    if django.VERSION < (1, 9):
        if relative_url.startswith('/'):
            return 'http://{}{}'.format(hostname, relative_url)
        else:
            return relative_url
    else:
        if relative_url.startswith('/'):
            return relative_url
        else:
            return '/{}'.format(relative_url)
