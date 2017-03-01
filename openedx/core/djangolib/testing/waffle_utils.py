"""
Test utilities when using waffle.
"""
from waffle.testutils import override_switch as waffle_override_switch
from request_cache.middleware import RequestCache, func_call_cache_key
from ..waffle_utils import is_switch_enabled


class override_switch(waffle_override_switch):  # pylint:disable=invalid-name
    """
    Subclasses waffle's override_switch in order clear the cache
    used on the is_switch_enabled function.
    """
    def _clear_cache(self):
        """
        Clears the requestcached values on the is_switch_enabled function.
        """
        cache_key = func_call_cache_key(is_switch_enabled.request_cached_contained_func, self.name)
        RequestCache.get_request_cache().data.pop(cache_key, None)

    def __enter__(self):
        self._clear_cache()
        super(override_switch, self).__enter__()

    def __exit__(self, *args, **kwargs):
        self._clear_cache()
        super(override_switch, self).__exit__(*args, **kwargs)
