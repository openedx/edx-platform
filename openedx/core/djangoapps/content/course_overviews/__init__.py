"""System for quickly accessing course metadata for use in "course dashboard" scenarios.

The rationale behind this app is that loading course metadata from the Split Mongo Modulestore is too slow. See:

    https://openedx.atlassian.net/wiki/pages/viewpage.action?spaceKey=MA&title=MA-296%3A+UserCourseEnrollmentList+Pe
    rformance+Investigation

This performance issue is not a problem when loading metadata for a *single* course; however, there are many cases
in LMS where we need to load metadata for a number of courses simultaneously, which can cause very noticeable
latency. Specifically, the endpoint /api/mobile_api/v0.5/users/{username}/course_enrollments takes an average of
900 ms, and all it does is generate a limited amount of data for no more than a few dozen courses per user.

Platform team plans to work on a long-term, generalized solution to this problem by improving the performance
of the modulestore using caching. Mobile team needed a more immediate solution, though, so what we've done here
is created the model CourseOverviewDescriptor, which resembles CourseDescriptor, but only has the attributes necessary
to display a course dashboard. The model is stored in a MySQL table, and serves as a cache for course metadata from the
actual module stores. Whenever a course is modified in Studio, we "invalidate the cache" by deleting the corresponding
CourseOverviewDescriptor (see signals.py).
"""

from xmodule.modulestore.django import modulestore

from .models import CourseOverviewDescriptor
# importing signals is necessary to activate signal handler
import signals  # pylint: disable=unused-import

def get_course_overview(course_id):
    """Return the CourseOverviewDescriptor for a given course ID.

    First, we try to load the CourseOverviewDescriptor the database. If it doesn't exist, we load the entire course from
    modulestore, create a CourseOverviewDescriptor from it, and then save it to the database for future use.
    """
    course_overview = None
    try:
        course_overview = CourseOverviewDescriptor.objects.get(id=course_id)
        # Cache hit!
    except CourseOverviewDescriptor.DoesNotExist:
        # Cache miss; load entire course and create a CourseOverviewDescriptor from it
        course = modulestore().get_course(course_id)
        if course:
            course_overview = CourseOverviewDescriptor.create_from_course(course)
            course_overview.save()
    return course_overview
