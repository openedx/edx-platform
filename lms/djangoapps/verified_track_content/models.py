"""
Models for verified track selections.
"""
from django.db import models
from django.utils.translation import ugettext_lazy
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from xmodule_django.models import CourseKeyField
from student.models import CourseEnrollment
from courseware.courses import get_course_by_id

from verified_track_content.tasks import sync_cohort_with_mode
from openedx.core.djangoapps.course_groups.cohorts import (
    get_course_cohorts, CourseCohort, is_course_cohorted, get_random_cohort
)

import logging

log = logging.getLogger(__name__)

DEFAULT_VERIFIED_COHORT_NAME = "Verified Learners"


@receiver(post_save, sender=CourseEnrollment)
def move_to_verified_cohort(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    If the learner has changed modes, update assigned cohort iff the course is using
    the Automatic Verified Track Cohorting MVP feature.
    """
    course_key = instance.course_id
    verified_cohort_enabled = VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key)
    verified_cohort_name = VerifiedTrackCohortedCourse.verified_cohort_name_for_course(course_key)

    if verified_cohort_enabled and (instance.mode != instance._old_mode):  # pylint: disable=protected-access
        if not is_course_cohorted(course_key):
            log.error("Automatic verified cohorting enabled for course '%s', but course is not cohorted.", course_key)
        else:
            course = get_course_by_id(course_key)
            existing_manual_cohorts = get_course_cohorts(course, CourseCohort.MANUAL)
            if any(cohort.name == verified_cohort_name for cohort in existing_manual_cohorts):
                # Get a random cohort to use as the default cohort (for audit learners).
                # Note that calling this method will create a "Default Group" random cohort if no random
                # cohort yet exist.
                random_cohort = get_random_cohort(course_key)
                args = {
                    'course_id': unicode(course_key),
                    'user_id': instance.user.id,
                    'verified_cohort_name': verified_cohort_name,
                    'default_cohort_name': random_cohort.name
                }
                # Do the update with a 3-second delay in hopes that the CourseEnrollment transaction has been
                # completed before the celery task runs. We want a reasonably short delay in case the learner
                # immediately goes to the courseware.
                sync_cohort_with_mode.apply_async(kwargs=args, countdown=3)

                # In case the transaction actually was not committed before the celery task runs,
                # run it again after 5 minutes. If the first completed successfully, this task will be a no-op.
                sync_cohort_with_mode.apply_async(kwargs=args, countdown=300)
            else:
                log.error(
                    "Automatic verified cohorting enabled for course '%s', "
                    "but verified cohort named '%s' does not exist.",
                    course_key,
                    verified_cohort_name,
                )


@receiver(pre_save, sender=CourseEnrollment)
def pre_save_callback(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Extend to store previous mode.
    """
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        instance._old_mode = old_instance.mode  # pylint: disable=protected-access
    except CourseEnrollment.DoesNotExist:
        instance._old_mode = None  # pylint: disable=protected-access


class VerifiedTrackCohortedCourse(models.Model):
    """
    Tracks which courses have verified track auto-cohorting enabled.
    """
    course_key = CourseKeyField(
        max_length=255, db_index=True, unique=True,
        help_text=ugettext_lazy(u"The course key for the course we would like to be auto-cohorted.")
    )

    verified_cohort_name = models.CharField(max_length=100, default=DEFAULT_VERIFIED_COHORT_NAME)

    enabled = models.BooleanField()

    def __unicode__(self):
        return u"Course: {}, enabled: {}".format(unicode(self.course_key), self.enabled)

    @classmethod
    def verified_cohort_name_for_course(cls, course_key):
        """
        Returns the given cohort name for the specific course.

        Args:
            course_key (CourseKey): a course key representing the course we want the verified cohort name for

        Returns:
            The cohort name if the course key has one associated to it. None otherwise.

        """
        try:
            config = cls.objects.get(course_key=course_key)
            return config.verified_cohort_name
        except cls.DoesNotExist:
            return None

    @classmethod
    def is_verified_track_cohort_enabled(cls, course_key):
        """
        Checks whether or not verified track cohort is enabled for the given course.

        Args:
            course_key (CourseKey): a course key representing the course we want to check

        Returns:
            True if the course has verified track cohorts is enabled
            False if not
        """
        try:
            return cls.objects.get(course_key=course_key).enabled
        except cls.DoesNotExist:
            return False
