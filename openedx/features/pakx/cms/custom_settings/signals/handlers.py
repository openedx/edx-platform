from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = getLogger(__name__)


@receiver(post_save, sender=CourseOverview, dispatch_uid="custom_settings.signals.handlers.initialize_course_settings")
def initialize_course_settings(sender, instance, created, **kwargs):
    """
    When ever a new course is created, add an honor mode for the given course so students can view certificates
    on their dashboard and progress page
    """

    if not created:
        return

    course_key = instance.id

    CourseMode.objects.get_or_create(
        course_id=course_key,
        mode_slug='honor',
        mode_display_name=instance.display_name
    )

    log.info("Course {} is added as honor mode".format(course_key))
