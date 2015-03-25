""" receiver of course_published events in order to trigger indexing task """
from datetime import datetime
from pytz import UTC

from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler

from .tasks import update_search_index


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """ Receives signal and kicks of celery task to update search index. """
    update_search_index.delay(unicode(course_key), datetime.now(UTC))
