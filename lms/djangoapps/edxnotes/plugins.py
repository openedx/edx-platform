"""
Registers the "edX Notes" feature for the edX platform.
"""


from django.conf import settings
from django.utils.translation import ugettext_noop

from lms.djangoapps.courseware.tabs import EnrolledTab


class EdxNotesTab(EnrolledTab):
    """
    The representation of the edX Notes course tab type.
    """

    type = "edxnotes"
    title = ugettext_noop("Notes")
    view_name = "edxnotes"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the edX Notes feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            user (User): the user interacting with the course
        """
        if not super(EdxNotesTab, cls).is_enabled(course, user=user):
            return False

        if not settings.FEATURES.get("ENABLE_EDXNOTES"):
            return False

        if user and not user.is_authenticated:
            return False

        return course.edxnotes
