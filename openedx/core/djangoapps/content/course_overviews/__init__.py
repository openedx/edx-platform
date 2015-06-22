"""
Library for quickly accessing basic course metadata.

The rationale behind this app is that loading course metadata from the Split
Mongo Modulestore is too slow. See:

    https://openedx.atlassian.net/wiki/pages/viewpage.action?spaceKey=MA&title=
    MA-296%3A+UserCourseEnrollmentList+Performance+Investigation

This performance issue is not a problem when loading metadata for a *single*
course; however, there are many cases in LMS where we need to load metadata
for a number of courses simultaneously, which can cause very noticeable
latency.
Specifically, the endpoint /api/mobile_api/v0.5/users/{username}/course_enrollments
took an average of 900 ms, and all it does is generate a limited amount of data
for no more than a few dozen courses per user.

In this app we declare the model CourseOverview, which caches course metadata
and a MySQL table and allows very quick access to it (according to NewRelic,
less than 1 ms). To load a CourseOverview, call CourseOverview.get_from_id
with the appropriate course key. The use cases for this app include things like
a user enrollment dashboard, a course metadata API, or a course marketing
page.
"""

# importing signals is necessary to activate signal handler, which invalidates
# the CourseOverview cache every time a course is published
import openedx.core.djangoapps.content.course_overviews.signals  # pylint: disable=unused-import
