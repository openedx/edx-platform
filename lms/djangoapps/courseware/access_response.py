"""
This file contains all the classes used by has_access for error handling
"""

from django.utils.translation import ugettext as _
from xmodule.course_metadata_utils import DEFAULT_START_DATE


class AccessResponse(object):
    """Class that represents a response from a has_access permission check."""
    def __init__(self, has_access, error_code=None, developer_message=None, user_message=None):
        """
        Creates an AccessResponse object.

        Arguments:
            has_access (bool): if the user is granted access or not
            error_code (String): optional - default is None. Unique identifier
                for the specific type of error
            developer_message (String): optional - default is None. Message
                to show the developer
            user_message (String): optional - default is None. Message to
                show the user
        """
        self.has_access = has_access
        self.error_code = error_code
        self.developer_message = developer_message
        self.user_message = user_message
        if has_access:
            assert error_code is None

    def __nonzero__(self):
        """
        Overrides bool().

        Allows for truth value testing of AccessResponse objects, so callers
        who do not need the specific error information can check if access
        is granted.

        Returns:
            bool: whether or not access is granted

        """
        return self.has_access

    def to_json(self):
        """
        Creates a serializable JSON representation of an AccessResponse object.

        Returns:
            dict: JSON representation
        """
        return {
            "has_access": self.has_access,
            "error_code": self.error_code,
            "developer_message": self.developer_message,
            "user_message": self.user_message
        }

    def __repr__(self):
        return "AccessResponse({!r}, {!r}, {!r}, {!r})".format(
            self.has_access,
            self.error_code,
            self.developer_message,
            self.user_message
        )


class AccessError(AccessResponse):
    """
    Class that holds information about the error in the case of an access
    denial in has_access. Contains the error code, user and developer
    messages. Subclasses represent specific errors.
    """
    def __init__(self, error_code, developer_message, user_message):
        """
        Creates an AccessError object.

        An AccessError object represents an AccessResponse where access is
        denied (has_access is False).

        Arguments:
            error_code (String): unique identifier for the specific type of
            error developer_message (String): message to show the developer
            user_message (String): message to show the user

        """
        super(AccessError, self).__init__(False, error_code, developer_message, user_message)


class StartDateError(AccessError):
    """
    Access denied because the course has not started yet and the user
    is not staff
    """
    def __init__(self, start_date):
        error_code = "course_not_started"
        if start_date == DEFAULT_START_DATE:
            developer_message = "Course has not started"
            user_message = _("Course has not started")
        else:
            developer_message = "Course does not start until {}".format(start_date)
            user_message = _("Course does not start until {}"  # pylint: disable=translation-of-non-string
                             .format("{:%B %d, %Y}".format(start_date)))
        super(StartDateError, self).__init__(error_code, developer_message, user_message)


class MilestoneError(AccessError):
    """
    Access denied because the user has unfulfilled milestones
    """
    def __init__(self):
        error_code = "unfulfilled_milestones"
        developer_message = "User has unfulfilled milestones"
        user_message = _("You have unfulfilled milestones")
        super(MilestoneError, self).__init__(error_code, developer_message, user_message)


class VisibilityError(AccessError):
    """
    Access denied because the user does have the correct role to view this
    course.
    """
    def __init__(self):
        error_code = "not_visible_to_user"
        developer_message = "Course is not visible to this user"
        user_message = _("You do not have access to this course")
        super(VisibilityError, self).__init__(error_code, developer_message, user_message)


class MobileAvailabilityError(AccessError):
    """
    Access denied because the course is not available on mobile for the user
    """
    def __init__(self):
        error_code = "mobile_unavailable"
        developer_message = "Course is not available on mobile for this user"
        user_message = _("You do not have access to this course on a mobile device")
        super(MobileAvailabilityError, self).__init__(error_code, developer_message, user_message)
