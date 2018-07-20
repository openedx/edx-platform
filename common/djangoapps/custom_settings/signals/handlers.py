from logging import getLogger
from django.db.models.signals import post_save
from django.dispatch import receiver
from course_modes.models import CourseMode
from custom_settings.models import CustomSettings
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.helpers import is_course_rereun

log = getLogger(__name__)


@receiver(post_save, sender=CourseOverview, dispatch_uid="custom_settings.signals.handlers.initialize_course_settings")
def initialize_course_settings(sender, instance, created, **kwargs):
    """
    When ever a new course is created
    1: We add a default entry for the given course in the CustomSettings Model
    2: We add a an honor mode for the given course so students can view certificates on their dashboard and progress page
    """

    if created:
        course_key = instance.id

        source_course_key = is_course_rereun(course_key)
        tags = ""
        if source_course_key:
            _settings = CustomSettings.objects.filter(id=source_course_key).first()
            tags = _settings.tags
            CustomSettings.objects.get_or_create(id=course_key, tags=tags)
        else:
            CustomSettings.objects.get_or_create(id=course_key)

        CourseMode.objects.get_or_create(
            course_id=course_key,
            mode_slug='honor',
            mode_display_name=instance.display_name)

        log.info("Course {} is set as not featured".format(course_key))
        log.info("Course {} is added as honor mode".format(course_key))
