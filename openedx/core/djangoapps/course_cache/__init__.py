
# TODO me: Finish docstrings on everything.
# TODO me: Eventually move course_overviews into this djangoapp, if they let me.

# Importing signals is necessary to activate signal handler, which invalidates
# the CourseOverview cache every time a course is published
from . import signals  # pylint: disable=unused-import
