import threading

_request_cache_threadlocal = threading.local()
_request_cache_threadlocal.data = {}

class RequestCache(object):
    @classmethod
    def get_request_cache(cls):
        return _request_cache_threadlocal
            
    def clear_request_cache(self):
        _request_cache_threadlocal.data = {}

    def process_request(self, request):
        self.clear_request_cache()
        return None

    def process_response(self, request, response):
        self.clear_request_cache()
        return response