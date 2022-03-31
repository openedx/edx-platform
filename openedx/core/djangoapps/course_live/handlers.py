"""
Signal handlers for course live app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..course_apps.signals import COURSE_APP_STATUS_INIT
from .models import CourseLiveConfiguration


@receiver(post_save, sender=CourseLiveConfiguration)
def post_save_handler(sender, **kwargs):
    """
    Whenever object is created or updated in CourseLiveConfiguration this handler will be trigred and It will
    create and/or update course_app status
    """
    course_live_config = kwargs.get('instance', None)
    COURSE_APP_STATUS_INIT.send(
        course_key=course_live_config.course_key,
        sender='lti_live',
        is_enabled=course_live_config.enabled
    )
