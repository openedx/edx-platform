"""
Signal receivers for the "student" application.
"""

# pylint: disable=unused-argument

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from lms.djangoapps.courseware.toggles import courseware_mfe_first_section_celebration_is_active
from common.djangoapps.student.helpers import EMAIL_EXISTS_MSG_FMT, USERNAME_EXISTS_MSG_FMT, AccountValidationError
from common.djangoapps.student.models import CourseEnrollment, CourseEnrollmentCelebration, is_email_retired, is_username_retired


@receiver(pre_save, sender=get_user_model())
def on_user_updated(sender, instance, **kwargs):
    """
    Check for retired usernames.
    """
    # Check only at User creation time and when not raw.
    if not instance.id and not kwargs['raw']:
        prefix_to_check = getattr(settings, 'RETIRED_USERNAME_PREFIX', None)
        if prefix_to_check:
            # Check for username that's too close to retired username format.
            if instance.username.startswith(prefix_to_check):
                raise AccountValidationError(
                    USERNAME_EXISTS_MSG_FMT.format(username=instance.username),
                    field="username"
                )

        # Check for a retired username.
        if is_username_retired(instance.username):
            raise AccountValidationError(
                USERNAME_EXISTS_MSG_FMT.format(username=instance.username),
                field="username"
            )

        # Check for a retired email.
        if is_email_retired(instance.email):
            raise AccountValidationError(
                EMAIL_EXISTS_MSG_FMT.format(email=instance.email),
                field="email"
            )


@receiver(post_save, sender=CourseEnrollment)
def create_course_enrollment_celebration(sender, instance, created, **kwargs):
    """
    Creates celebration rows when enrollments are created

    This is how we distinguish between new enrollments that we want to celebrate and old ones
    that existed before we introduced a given celebration.
    """
    if not created:
        return

    # The UI for celebrations is only supported on the MFE right now, so don't turn on
    # celebrations unless this enrollment's course is MFE-enabled and has milestones enabled.
    if not courseware_mfe_first_section_celebration_is_active(instance.course_id):
        return

    try:
        CourseEnrollmentCelebration.objects.create(
            enrollment=instance,
            celebrate_first_section=True,
        )
    except IntegrityError:
        # A celebration object was already created. Shouldn't happen, but ignore it if it does.
        pass
