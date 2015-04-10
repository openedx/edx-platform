""" receiver of course_published events in order to trigger indexing task """
from datetime import datetime
from pytz import UTC

from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler
from contentstore.courseware_index import indexing_is_enabled


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update search index
    """
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from .tasks import update_search_index
    if indexing_is_enabled():
        update_search_index.delay(unicode(course_key), datetime.now(UTC).isoformat())
