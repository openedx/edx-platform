"""
Signal handler for setting default course verification dates
"""
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import VerificationDeadline


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    sets the verification deadline date to a default.
    """
    course = modulestore().get_course(course_key)
    if course:
        try:
            deadline = VerificationDeadline.objects.get(course_key=course_key)
            if not deadline.deadline_is_explicit and deadline.deadline != course.end:
                VerificationDeadline.set_deadline(course_key, course.end)
        except ObjectDoesNotExist:
            VerificationDeadline.set_deadline(course_key, course.end)
