import logging
from django.core.cache import cache, get_cache
from datetime import datetime

def _get_discussion_cache():
    return get_cache('mongo_metadata_inheritance')


def get_discussion_cache_key(course_id):
    return 'discussion_items_{0}'.format(course_id)


def get_discussion_cache_entry(modulestore, course_id):
    cache_entry = None
    cache = _get_discussion_cache()
    
    if cache is not None:
        cache_entry = cache.get(get_discussion_cache_key(course_id), None)
        # @todo: add expiry here
    
    if cache_entry is None:
        cache_entry = generate_discussion_cache_entry(modulestore, course_id)

    return cache_entry.get('modules',[])


def generate_discussion_cache_entry(modulestore, course_id):
    components = course_id.split('/')
    all_discussion_modules = modulestore.get_items(['i4x', components[0], components[1], 'discussion', None], 
        course_id=course_id)

    cache = _get_discussion_cache()
    entry = {'modules': all_discussion_modules, 'timestamp': datetime.now()}
    logging.debug('**** entry = {0}'.format(entry))
    if cache is not None:
        cache.set(get_discussion_cache_key(course_id), entry)
    return entry


def modulestore_update_signal_handler(modulestore = None, course_id = None, location = None, **kwargs):
    """called when there is an write event in our modulestore
    """
    if location.category == 'discussion':
        logging.debug('******* got modulestore update signal. Regenerating discussion cache for {0}'.format(course_id))
        # refresh the cache entry if we've changed a discussion module
        generate_discussion_cache_entry(modulestore, course_id)


def discussion_cache_register_for_updates(modulestore):
    if modulestore.modulestore_update_signal is not None:
        modulestore.modulestore_update_signal.connect(modulestore_update_signal_handler)