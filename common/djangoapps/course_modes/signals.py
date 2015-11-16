"""
Signal handler for setting default course mode expiration dates
"""
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import CourseMode, CourseModeAutoExpirationConfiguration


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    sets the verified mode dates to defaults.
    """
    try:
        verified_mode = CourseMode.objects.get(course_id=course_key, mode_slug=CourseMode.VERIFIED)
        if _should_update_date(verified_mode):
            course = modulestore().get_course(course_key)
            verification_window = CourseModeAutoExpirationConfiguration.current().verification_window

            verified_mode.expiration_datetime = course.end - verification_window
            verified_mode.save()
    except ObjectDoesNotExist:
        pass


def _should_update_date(verified_mode):
    """ Returns whether or not the verified mode should be updated. """
    return not(verified_mode is None or verified_mode.expiration_datetime_is_explicit)
