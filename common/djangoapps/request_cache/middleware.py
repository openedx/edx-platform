import threading

_request_cache_threadlocal = threading.local()
_request_cache_threadlocal.data = {}
_request_cache_threadlocal.request = None


class RequestCache(object):
    @classmethod
    def get_request_cache(cls):
        return _request_cache_threadlocal

    @classmethod
    def get_current_request(cls):
        """
        Get a reference to the HttpRequest object, if we are presently
        servicing one.
        """
        return _request_cache_threadlocal.request

    @classmethod
    def clear_request_cache(cls):
        """
        Empty the request cache.
        """
        _request_cache_threadlocal.data = {}
        _request_cache_threadlocal.request = None

    def process_request(self, request):
        self.clear_request_cache()
        _request_cache_threadlocal.request = request
        return None

    def process_response(self, request, response):
        self.clear_request_cache()
        return response
