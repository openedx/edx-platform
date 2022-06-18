from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.settings import extensions_api_settings


class BaseCacheResponseMixin:
    # todo: test me. Create generic test like
    # test_cache_reponse(view_instance, method, should_rebuild_after_method_evaluation)
    object_cache_key_func = extensions_api_settings.DEFAULT_OBJECT_CACHE_KEY_FUNC
    list_cache_key_func = extensions_api_settings.DEFAULT_LIST_CACHE_KEY_FUNC
    object_cache_timeout = extensions_api_settings.DEFAULT_CACHE_RESPONSE_TIMEOUT
    list_cache_timeout = extensions_api_settings.DEFAULT_CACHE_RESPONSE_TIMEOUT


class ListCacheResponseMixin(BaseCacheResponseMixin):
    @cache_response(key_func='list_cache_key_func', timeout='list_cache_timeout')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RetrieveCacheResponseMixin(BaseCacheResponseMixin):
    @cache_response(key_func='object_cache_key_func', timeout='object_cache_timeout')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CacheResponseMixin(RetrieveCacheResponseMixin,
                         ListCacheResponseMixin):
    pass
