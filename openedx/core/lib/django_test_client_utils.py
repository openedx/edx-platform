"""
This file includes util methods.
"""


def get_absolute_url(path):
    """ Generate an absolute URL for a resource on the test server. """
    return u'http://testserver/{}'.format(path.lstrip(u'/'))
