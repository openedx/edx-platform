"""
This file contains all the classes used by has_access for error handling
"""


class AccessResponse(object):
    """Class that represents a response from a has_access permission check."""
    def __init__(self, has_access, error_code=None, developer_message=None, user_message=None):
        """
        :param has_access (bool): if the user is granted access or not
        :param error_code (String): optional - default is None. unique identifier for the specific type of error
        :param developer_message (String): optional - default is None. message to show the developer
        :param user_message (String): optional - default is None. message to show the user
        """
        self.has_access = has_access
        self.error_code = error_code
        self.developer_message = developer_message
        self.user_message = user_message
        if has_access:
            assert error_code is None

    def __nonzero__(self):
        """Overrides bool() to correct truth value testing"""
        return self.has_access

    def to_json(self):
        """Returns json representation of this AccessResponse"""
        return {
            "has_access": self.has_access,
            "error_code": self.error_code,
            "developer_message": self.developer_message,
            "user_message": self.user_message
        }


class AccessError(AccessResponse):
    """
    Class that holds information about the error in the case of an access denial in has_access.
    Contains the error code, user and developer messages. Subclasses represent specific errors.
    """
    def __init__(self, error_code, developer_message, user_message):
        """
        :param: error_code (String): unique identifier for the specific type of error
        :param: developer_message (String): message to show the developer
        :param: user_message (String): message to show the user

        """
        super(AccessError, self).__init__(False, error_code, developer_message, user_message)


class StartDateError(AccessError):
    """Access denied because the course has not started yet and the user is not staff"""
    def __init__(self, start_message):
        error_code = "course_not_started"
        developer_message = "Course does not start until {start}  \
                            and user does not have staff access".format(start=start_message)
        user_message = start_message
        super(StartDateError, self).__init__(error_code, developer_message, user_message)


class MilestoneError(AccessError):
    """Access denied because the user hasn't completed the needed milestones (pre-reqs/entrance exams)."""
    def __init__(self):
        error_code = "unfulfilled milestones"
        developer_message = "User has not completed the necessary milestones"
        user_message = "You have uncompleted milestones"
        super(MilestoneError, self).__init__(error_code, developer_message, user_message)


class VisibilityError(AccessError):
    """Access denied because the course is only visible to staff and the user is not staff"""
    def __init__(self):
        error_code = "visible_to_staff_only"
        developer_message = "Course is only visible to staff and user is not staff"
        user_message = "Course is not visible to you"
        super(VisibilityError, self).__init__(error_code, developer_message, user_message)


class MobileAvailabilityError(AccessError):
    """Access denied because the course is not available on mobile and the user is not a beta tester or staff"""
    def __init__(self):
        error_code = "mobile_unavailable"
        developer_message = "Course is not available on mobile for this user"
        user_message = "You cannot view this course on mobile"
        super(MobileAvailabilityError, self).__init__(error_code, developer_message, user_message)
