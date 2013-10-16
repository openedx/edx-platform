"""
Implement a request scoped cache which is setup and torn down after every request
"""
import threading

_request_cache_threadlocal = threading.local()
_request_cache_threadlocal.data = {}


class RequestCache(object):
    """
    Implementation of a request scoped cache
    """
    @classmethod
    def get_request_cache(cls):
        """
        Returns the data associated with the threadlocal
        """
        return _request_cache_threadlocal

    def clear_request_cache(self):
        """
        Resets the content in the threadlocal
        """
        _request_cache_threadlocal.data = {}

    def process_request(self, request):
        """
        Django middleware entry point for request processing
        """
        self.clear_request_cache()
        return None

    def process_response(self, request, response):
        """
        Django middleware entry point for response processing
        """
        self.clear_request_cache()
        return response