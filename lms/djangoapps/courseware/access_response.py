"""
This file contains all the classes used by has_access for error handling
"""


from django.utils.translation import ugettext as _

from xmodule.course_metadata_utils import DEFAULT_START_DATE


class AccessResponse(object):
    """Class that represents a response from a has_access permission check."""
    def __init__(self, has_access, error_code=None, developer_message=None, user_message=None,
                 additional_context_user_message=None, user_fragment=None):
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
            additional_context_user_message (String): optional - default is None. Message to
                show the user when additional context like the course name is necessary
            user_fragment (:py:class:`~web_fragments.fragment.Fragment`): optional -
                An html fragment to display to the user if their access is denied
        """
        self.has_access = has_access
        self.error_code = error_code
        self.developer_message = developer_message
        self.user_message = user_message
        self.additional_context_user_message = additional_context_user_message
        self.user_fragment = user_fragment
        if has_access:
            assert error_code is None

    def __bool__(self):
        """
        Overrides bool().

        Allows for truth value testing of AccessResponse objects, so callers
        who do not need the specific error information can check if access
        is granted.

        Returns:
            bool: whether or not access is granted

        """
        return self.has_access

    __nonzero__ = __bool__

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
            "user_message": self.user_message,
            "additional_context_user_message": self.additional_context_user_message,
            "user_fragment": self.user_fragment,
        }

    def __repr__(self):
        return "AccessResponse({!r}, {!r}, {!r}, {!r}, {!r}, {!r})".format(
            self.has_access,
            self.error_code,
            self.developer_message,
            self.user_message,
            self.additional_context_user_message,
            self.user_fragment,
        )

    def __eq__(self, other):
        if not isinstance(other, AccessResponse):
            return False

        return (
            self.has_access == other.has_access and
            self.error_code == other.error_code and
            self.developer_message == other.developer_message and
            self.user_message == other.user_message and
            self.additional_context_user_message == other.additional_context_user_message and
            self.user_fragment == other.user_fragment
        )


class AccessError(AccessResponse):
    """
    Class that holds information about the error in the case of an access
    denial in has_access. Contains the error code, user and developer
    messages. Subclasses represent specific errors.
    """
    def __init__(self, error_code, developer_message, user_message,
                 additional_context_user_message=None, user_fragment=None):
        """
        Creates an AccessError object.

        An AccessError object represents an AccessResponse where access is
        denied (has_access is False).

        Arguments:
            error_code (String): unique identifier for the specific type of
            error developer_message (String): message to show the developer
            user_message (String): message to show the user
            additional_context_user_message (String): message to show user with additional context like the course name
            user_fragment (:py:class:`~web_fragments.fragment.Fragment`): HTML to show the user

        """
        super(AccessError, self).__init__(False, error_code, developer_message, user_message,
                                          additional_context_user_message, user_fragment)


class StartDateError(AccessError):
    """
    Access denied because the course has not started yet and the user
    is not staff
    """
    def __init__(self, start_date, display_error_to_user=True):
        """
        Arguments:
            display_error_to_user: If True, display this error to users in the UI.
        """
        error_code = "course_not_started"
        if start_date == DEFAULT_START_DATE:
            developer_message = u"Course has not started"
            user_message = _(u"Course has not started")
        else:
            developer_message = u"Course does not start until {}".format(start_date)
            user_message = _(u"Course does not start until {}"
                             .format(u"{:%B %d, %Y}".format(start_date)))
        super(StartDateError, self).__init__(
            error_code,
            developer_message,
            user_message if display_error_to_user else None
        )


class MilestoneAccessError(AccessError):
    """
    Access denied because the user has unfulfilled milestones
    """
    def __init__(self):
        error_code = "unfulfilled_milestones"
        developer_message = u"User has unfulfilled milestones"
        user_message = _(u"You have unfulfilled milestones")
        super(MilestoneAccessError, self).__init__(error_code, developer_message, user_message)


class VisibilityError(AccessError):
    """
    Access denied because the user does have the correct role to view this
    course.
    """
    def __init__(self, display_error_to_user=True):
        """
        Arguments:
            display_error_to_user: Should a message showing that access was denied to this content
                be shown to the user?
        """
        error_code = "not_visible_to_user"
        developer_message = u"Course is not visible to this user"
        user_message = _(u"You do not have access to this course")
        super(VisibilityError, self).__init__(
            error_code,
            developer_message,
            user_message if display_error_to_user else None
        )


class MobileAvailabilityError(AccessError):
    """
    Access denied because the course is not available on mobile for the user
    """
    def __init__(self):
        error_code = "mobile_unavailable"
        developer_message = u"Course is not available on mobile for this user"
        user_message = _(u"You do not have access to this course on a mobile device")
        super(MobileAvailabilityError, self).__init__(error_code, developer_message, user_message)


class IncorrectPartitionGroupError(AccessError):
    """
    Access denied because the user is not in the correct user subset.
    """
    def __init__(self, partition, user_group, allowed_groups, user_message=None, user_fragment=None):
        error_code = "incorrect_user_group"
        developer_message = u"In partition {}, user was in group {}, but only {} are allowed access".format(
            partition.name,
            user_group.name if user_group is not None else user_group,
            u", ".join(group.name for group in allowed_groups),
        )
        super(IncorrectPartitionGroupError, self).__init__(
            error_code=error_code,
            developer_message=developer_message,
            user_message=user_message,
            user_fragment=user_fragment
        )


class NoAllowedPartitionGroupsError(AccessError):
    """
    Access denied because the content is not allowed to any group in a partition.
    """
    def __init__(self, partition, user_message=None, user_fragment=None):
        error_code = "no_allowed_user_groups"
        developer_message = u"Group access for {} excludes all students".format(partition.name)
        super(NoAllowedPartitionGroupsError, self).__init__(error_code, developer_message, user_message)


class EnrollmentRequiredAccessError(AccessError):
    """
    Access denied because the user must be enrolled in the course
    """
    def __init__(self):
        error_code = "enrollment_required"
        developer_message = u"User must be enrolled in the course"
        user_message = _(u"You must be enrolled in the course")
        super(EnrollmentRequiredAccessError, self).__init__(error_code, developer_message, user_message)


class AuthenticationRequiredAccessError(AccessError):
    """
    Access denied because the user must be authenticated to see it
    """
    def __init__(self):
        error_code = "authentication_required"
        developer_message = u"User must be authenticated to view the course"
        user_message = _(u"You must be logged in to see this course")
        super(AuthenticationRequiredAccessError, self).__init__(error_code, developer_message, user_message)


class CoursewareMicrofrontendDisabledAccessError(AccessError):
    """
    Access denied because the courseware micro-frontend is disabled for this user.
    """
    def __init__(self):
        error_code = 'microfrontend_disabled'
        developer_message = u'Micro-frontend is disabled for this user'
        user_message = _(u'Please view your course in the existing experience')
        super(CoursewareMicrofrontendDisabledAccessError, self).__init__(error_code, developer_message, user_message)
