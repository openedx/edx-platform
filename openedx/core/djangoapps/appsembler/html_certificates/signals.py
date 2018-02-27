"""
Appsembler's signals to customize certificates and course behaviour
"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler

from course_modes.models import CourseMode

@receiver(SignalHandler.course_published)
def set_default_mode_on_course_publish(sender, course_key, **kwargs): # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and
    creates a CourseMode in the default mode
    """
    default_mode, created = CourseMode.objects.get_or_create(
        course_id=course_key,
        mode_slug=settings.DEFAULT_COURSE_MODE_SLUG,
        mode_display_name=settings.DEFAULT_MODE_NAME_FROM_SLUG
    )
