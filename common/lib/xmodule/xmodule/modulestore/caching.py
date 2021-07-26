"""
Different ModuleStores have their own internal caching, but this module is for
caching mechanisms that cut across the various ModuleStores (see the class
docstrings for more detailed explanations).
"""
from collections import defaultdict

from edx_django_utils.cache import RequestCache


class ModuleStoreCache:
    """
    Used to ModuleStore queries (for now, just get_course) at a request level.

    This uses a RequestCache underneath, but tries to present a higher-level
    interface.

    You might be wondering, "Why does this class exist? Why not make caching an
    internal implementation detail of any given ModuleStore?" The answer is that
    CCX works by mutating the course that is returned by the
    DraftVersioningModuleStore (a.k.a. "Split Mongo"), and replacing its various
    UsageKeys and field data to convert them into CCX Usage Keys and overrides.
    But because those mutate the courses being passed back, it means that if we
    were to cache it at the DraftVersioningModuleStore level, we'd store it in
    the cache by its "base course" key ("course-v1:..."), but it would be
    mutated in-place to be the contents of the derived CCX ("ccx-v1:..."), and
    the results for subsequent cache hits would be incorrect.

    To get around this limitation, we have to do the caching at at outer layer,
    after CCX has done its mutations. Since CCX works with a wrapper class that
    proxies most calls to the wrapped ModuleStore (CCXModulestoreWrapper), we
    can do the same thing (see CachingModuleStoreWrapper).

    That works great for caching the value, but it makes invalidation trickier.
    We _could_ make CachingModuleStoreWrapper understand every ModuleStore call
    that could lead to the course being invalidated, but that's brittle and
    error prone. But the underlying ModuleStores themselves know _exactly_ when
    data is being changed, because doing so is an explicit write that they have
    to perform.

    That's why we have an explicit ModuleStoreCache object. We create an
    instance of this object for the CachingModuleStoreWrapper layer to use to
    get courses from the cache and add courses to the cache, but then we pass
    that same instance of ModuleStoreCache to the underlying ModuleStores,
    because they will know how to _invalidate_ the cache entries for a given
    course when writes occur.
    """
    def __init__(self):
        """Init our namespaced request cache."""
        self._request_cache = RequestCache('ModuleStoreCache')

    def get_course(self, course_key, depth):
        cache_key = (course_key, depth)
        return self._request_cache.get_cached_response(cache_key)

    def update_course(self, course_key, depth, course):
        cache_key = (course_key, depth)
        self._request_cache.set(cache_key, course)

    def invalidate_course(self, course_key):
        # Remember that there may be multiple keys for the same course
        cache_keys_to_del = [
            cache_key
            for cache_key in self._request_cache.data
            if cache_key[0] == course_key  # cache_key is (course_key, depth)
        ]
        for cache_key in cache_keys_to_del:
            self._request_cache.delete(cache_key)


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
        # no advanced params. This is the vast, vast majority of queries, so
        # it's not really worth figuring out how to correctly handle the kwargs
        # cases.
        use_cache = not kwargs
        if use_cache:
            cache_response = self._modulestore_cache.get_course(course_key, depth)
            if cache_response.is_found:
                print(f"Cache hit for {course_key}!")
                return cache_response.value

        course = self._modulestore.get_course(course_key, depth, **kwargs)
        if use_cache:
            self._modulestore_cache.update_course(course_key, depth, course)

        return course
