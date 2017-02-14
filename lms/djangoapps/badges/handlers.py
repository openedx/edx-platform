"""
Badges related signal handlers.
"""
from django.dispatch import receiver

from lms.djangoapps.badges.events.course_meta import award_enrollment_badge
from lms.djangoapps.badges.utils import badges_enabled
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange


@receiver(ENROLL_STATUS_CHANGE)
def award_badge_on_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Awards enrollment badge to the given user on new enrollments.
    """
    if badges_enabled and event == EnrollStatusChange.enroll:
        award_enrollment_badge(user)
