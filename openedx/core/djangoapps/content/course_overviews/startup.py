"""Code run at server start up to initialize the course_overviews app."""

# Importing signals is necessary to activate signal handler, which invalidates
# the CourseOverview cache every time a course is published.
import openedx.core.djangoapps.content.course_overviews.signals  # pylint: disable=unused-import
