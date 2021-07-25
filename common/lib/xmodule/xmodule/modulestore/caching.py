"""
Different ModuleStores have their own internal caching mechanisms, but sometimes
we need utilities that can be used across multiple ModuleStore types.
"""
from collections import defaultdict
from edx_django_utils.cache import RequestCache


class ModuleStoreCache:
    """
    Used to cache certain ModuleStore queries at a request level.

    This uses a RequestCache underneath, but tries to present a higher-level
    interface.
    """
    def __init__(self):
        self._request_cache = RequestCache('CachingModulestoreWrapper')
        self._courses_to_depths = defaultdict(set)

    def get_course(self, course_key, depth):
        cache_key = (course_key, depth)
        return self._request_cache.get_cached_response(cache_key)

    def update_course(self, course_key, depth, course):
        cache_key = (course_key, depth)
        self._request_cache.set(cache_key, course)
        self._courses_to_depths[course_key].add(depth)

    def invalidate_course(self, course_key):
        # Remember that there may be multiple keys for the same course
        for depth in self._courses_to_depths[course_key]:
            cache_key = (course_key, depth)
            self._request_cache.delete(cache_key)
        self._courses_to_depths[cache_key] = set()

class CachingModuleStoreWrapper:
    """
    Wrap a modulestore and add request-level caching of get_course()

    This class proxies most of its requests to its underlying Modulestore
    object. It was necessary to do this as a separate wrapping layer because
    our _MIXED_MODULESTORE can be a CCXModulestoreWrapper or a MixedModuleStore
    depending on our settings. Putting this caching into MixedModuleStore itself
    doesn't work because of the way CCXModulestoreWrapper pulls back results
    from MixedModuleStore and changes their usage keys.

    So yes, this means that content access is layered behind proxies like:

      CachingModuleStoreWrapper ->
        (CCXModulestoreWrapper -> if CCX enabled)
          MixedModuleStore ->
            DraftVersioningModuleStore (Split Mongo)
            DraftModuleStore (Old Mongo)
    """
    def __init__(self, modulestore_obj, modulestore_cache):
        self.__dict__['_modulestore'] = modulestore_obj
        self.__dict__['_modulestore_cache'] = modulestore_cache

    def __getattr__(self, name):
        """Look up missing attributes on the wrapped modulestore"""
        return getattr(self._modulestore, name)

    def __setattr__(self, name, value):
        """Set attributes only on the wrapped modulestore"""
        setattr(self._modulestore, name, value)

    def __delattr__(self, name):
        """Delete attributes only on the wrapped modulestore"""
        delattr(self._modulestore, name)

    def get_course(self, course_key, depth=0, **kwargs):
        """
        Call get_course on wrapped modulestore, but with request-caching.

        This is the only call that actually _uses_ caching at this layer.
        """
        # Only use the request cache if we're dealing with a simple query with
        # no advanced params. (This is the vast, vast majority of queries.)
        use_cache = not kwargs
        if use_cache:
            cache_response = self._modulestore_cache.get_course(course_key, depth)
            if cache_response.is_found:
                return cache_response.value

        course = self._modulestore.get_course(course_key, depth, **kwargs)
        if use_cache:
            self._modulestore_cache.update_course(course_key, depth, course)

        return course