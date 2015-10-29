"""
Importing signals to activate signal handler, which invalidates
the CourseOverview cache every time a course is published
"""
import openedx.core.djangoapps.content.course_overviews.signals  # pylint: disable=unused-import
