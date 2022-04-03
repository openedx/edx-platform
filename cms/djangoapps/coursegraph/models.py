"""
(Proxy) models supporting CourseGraph.
"""

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseGraphCourseDump(CourseOverview):
    """
    Proxy model for CourseOverview.

    Does *not* create/update/delete CourseOverview objects - only reads the objects.
    Uses the course IDs of the CourseOverview objects to determine which courses
    can be dumped to CourseGraph.
    """
    class Meta:
        proxy = True

    def __str__(self):
        """Represent ourselves with the course key."""
        return str(self.id)
