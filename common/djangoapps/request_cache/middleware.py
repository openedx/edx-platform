"""
An implementation of a RequestCache. This cache is reset at the beginning
and end of every request.
"""

import crum
import threading


class _RequestCache(threading.local):
    """
    A thread-local for storing the per-request cache.
    """
    def __init__(self):
        super(_RequestCache, self).__init__()
        self.data = {}


REQUEST_CACHE = _RequestCache()


class RequestCache(object):
    @classmethod
    def get_request_cache(cls, name=None):
        """
        This method is deprecated. Please use :func:`request_cache.get_cache`.
        """
        if name is None:
            return REQUEST_CACHE
        else:
            return REQUEST_CACHE.data.setdefault(name, {})

    @classmethod
    def get_current_request(cls):
        """
        This method is deprecated. Please use :func:`request_cache.get_request`.
        """
        return crum.get_current_request()

    @classmethod
    def clear_request_cache(cls):
        """
        Empty the request cache.
        """
        REQUEST_CACHE.data = {}

    def process_request(self, request):
        self.clear_request_cache()
        return None

    def process_response(self, request, response):
        self.clear_request_cache()
        return response

    def process_exception(self, request, exception):  # pylint: disable=unused-argument
        """
        Clear the RequestCache after a failed request.
        """
        self.clear_request_cache()
        return None
