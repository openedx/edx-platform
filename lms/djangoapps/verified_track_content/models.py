"""
Models for verified track selections.
"""
from django.db import models
from django.utils.translation import ugettext_lazy

from xmodule_django.models import CourseKeyField


class VerifiedTrackCohortedCourse(models.Model):
    """
    Tracks which courses have verified track auto-cohorting enabled.
    """
    course_key = CourseKeyField(
        max_length=255, db_index=True, unique=True,
        help_text=ugettext_lazy(u"The course key for the course we would like to be auto-cohorted.")
    )

    enabled = models.BooleanField()

    def __unicode__(self):
        return u"Course: {}, enabled: {}".format(unicode(self.course_key), self.enabled)

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
