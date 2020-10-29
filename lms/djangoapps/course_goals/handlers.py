"""
Signal handlers for course goals.
"""


import six
from django.db import models
from django.dispatch import receiver

import six
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment

from .api import add_course_goal, remove_course_goal
from .models import GOAL_KEY_CHOICES


@receiver(models.signals.post_save, sender=CourseEnrollment, dispatch_uid="update_course_goal_on_enroll_change")
def update_course_goal_on_enroll_change(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Updates goals as follows on enrollment changes:
    1) Set the course goal to 'certify' when the user enrolls as a verified user.
    2) Remove the course goal when the user's enrollment is no longer active.
    """
    course_id = six.text_type(instance.course_id)
    if not instance.is_active:
        remove_course_goal(instance.user, course_id)
    elif instance.mode == CourseMode.VERIFIED:
        add_course_goal(instance.user, course_id, GOAL_KEY_CHOICES.certify)
