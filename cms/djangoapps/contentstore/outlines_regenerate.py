"""
Defines a proxy model to enable a Django admin interface to trigger asynch
tasks which regenerates course outline data.
"""
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseOutlineRegenerate(CourseOverview):
    """
    Proxy model for CourseOverview.

    Does *not* create/update/delete CourseOverview objects - only reads the objects.
    Uses the course IDs of the CourseOverview objects to determine which course
    outlines to regenerate.
    """
    class Meta:
        proxy = True

    def __str__(self):
        """Represent ourselves with the course key."""
        return str(self.id)

    @classmethod
    def get_course_outline_ids(cls):
        """
        Returns all the CourseOverview object ids.
        """
        return cls.objects.values_list('id', flat=True)
