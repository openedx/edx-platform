"""
Signal handler for posting course updated to CCXCon
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published, dispatch_uid='ccxcon_course_publish_handler')
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Listener for course_plublish events.
    This listener takes care of submitting a task to update CCXCon
    """
    # update the course information on ccxcon using celery
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from openedx.core.djangoapps.ccxcon import tasks
    tasks.update_ccxcon.delay(unicode(course_key))
