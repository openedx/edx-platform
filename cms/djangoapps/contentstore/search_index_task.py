""" receiver of course_published / item_published events in order to trigger indexing task """
from django.dispatch import receiver
from celery.task import task
from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.courseware_index import CoursewareSearchIndexer, SearchIndexingError
from celery.utils.log import get_task_logger

LOGGER = get_task_logger(__name__)
FULL_COURSE_REINDEX_THRESHOLD = 1


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, item_keys=None, **kwargs):  # pylint: disable=unused-argument
    """ Receives signal and kicks of celery task to update search index. """
    update_search_index.delay(course_key, item_keys)


@task()
def update_search_index(course_key, item_keys=None):
    """ Updates course search index. """
    def index_location(location):
        """ Adds location to the courseware search index """
        CoursewareSearchIndexer.add_to_search_index(modulestore(), location, delete=False, raise_on_error=True)

    try:
        if item_keys and len(item_keys) <= FULL_COURSE_REINDEX_THRESHOLD:
            for item_key in item_keys:
                index_location(item_key)
        else:
            index_location(course_key)

    except SearchIndexingError as exc:
        if item_keys:
            LOGGER.error(
                'Search indexing error for items %s in course %s - %s',
                ','.join(item_keys),
                course_key,
                unicode(exc)
            )
        else:
            LOGGER.error('Search indexing error for complete course %s - %s', course_key, unicode(exc))
    else:
        if item_keys:
            LOGGER.debug('Search indexing successful for items %s in course %s', ','.join(item_keys), course_key)
        else:
            LOGGER.debug('Search indexing successful for complete course %s', course_key)
