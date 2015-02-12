from django.dispatch import receiver
from celery.task import task
from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.courseware_index import CoursewareSearchIndexer, SearchIndexingError
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):
    """ Receives signal and kicks of celery task to update search index. """
    update_search_index.delay(course_key)

@task()
def update_search_index(course_key):
    """ Updates course search index. """
    try:
        CoursewareSearchIndexer.add_to_search_index(modulestore(), course_key, delete=False, raise_on_error=True)
    except SearchIndexingError as exc:
        logger.error('Search indexing error for course %s - %s', course_key, unicode(exc))
    else:
        logger.debug('Search indexing successful for course %s', course_key)
