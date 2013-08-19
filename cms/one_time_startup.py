from dogapi import dog_http_api, dog_stats_api
from django.conf import settings
from xmodule.modulestore.django import modulestore
from django.dispatch import Signal
from request_cache.middleware import RequestCache

from django.core.cache import get_cache

CACHE = get_cache('mongo_metadata_inheritance')
for store_name in settings.MODULESTORE:
    store = modulestore(store_name)

    store.set_modulestore_configuration({
        'metadata_inheritance_cache_subsystem': CACHE,
        'request_cache': RequestCache.get_request_cache()
    })

    modulestore_update_signal = Signal(providing_args=['modulestore', 'course_id', 'location'])
    store.modulestore_update_signal = modulestore_update_signal
if hasattr(settings, 'DATADOG_API'):
    dog_http_api.api_key = settings.DATADOG_API
    dog_stats_api.start(api_key=settings.DATADOG_API, statsd=True)
