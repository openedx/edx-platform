import sys

from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve


class UrlResetMixin(object):
    """Mixin to reset urls.py before and after a test

    Django memoizes the function that reads the urls module (whatever module
    urlconf names). The module itself is also stored by python in sys.modules.
    To fully reload it, we need to reload the python module, and also clear django's
    cache of the parsed urls.

    However, the order in which we do this doesn't matter, because neither one will
    get reloaded until the next request

    Doing this is expensive, so it should only be added to tests that modify settings
    that affect the contents of urls.py
    """

    def _reset_urls(self, urlconf=None):
        if urlconf is None:
            urlconf = settings.ROOT_URLCONF

        if urlconf in sys.modules:
            reload(sys.modules[urlconf])
        clear_url_caches()

        # Resolve a URL so that the new urlconf gets loaded
        resolve('/')

    def setUp(self, **kwargs):
        """Reset django default urlconf before tests and after tests"""
        super(UrlResetMixin, self).setUp(**kwargs)
        self._reset_urls()
        self.addCleanup(self._reset_urls)
