class AccessResponse(object):
    """Class that represents a response from a has_access permission check."""
    def __init__(self, has_access, access_error):
        """
        :param has_access (bool): if the user is granted access or not
        :param access_error (AccessError): None if granted access or in certain cases of denied access, otherwise
                                        contains specific information on why access was denied
        """
        self.has_access = has_access
        self.access_error = access_error
        if has_access:
            assert access_error is None

    def __nonzero__(self):
        """Overrides bool() to correct truth value testing"""
        return self.has_access

    def __eq__(self, other):
        return (
            isinstance(other, AccessResponse) and
            self.has_access == other.has_access and
            self.access_error == other.access_error
        )

    def __hash__(self):
        return hash((self.has_access, self.access_error))

    def to_json(self):
        """Returns json representation of this AccessResponse"""
        return {
            "has_access": self.has_access,
            "access_error": self.access_error.to_json() if self.access_error is not None else None
        }


class AccessError(object):
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
        self.error_code = error_code
        self.developer_message = developer_message
        self.user_message = user_message

    def __eq__(self, other):
        return (
            isinstance(other, AccessError) and
            self.error_code == other.error_code and
            self.user_message == other.user_message and
            self.developer_message == other.developer_message
        )

    def __hash__(self):
        return hash((self.error_code, self.developer_message, self.user_message))

    def to_json(self):
        """Returns json representation of this AccessError"""
        return {
            "error_code": self.error_code,
            "developer_message": self.developer_message,
            "user_message": self.user_message
        }


class StartDateError(AccessResponse):
    """
    Subclasses AccessResponse
    Access denied because the course has not started yet and the user is not staff
    """
    def __init__(self, user_message):
        error_code = "course_not_started"
        developer_message = "Course does not start until {start} and user does not have staff access".format(start=user_message)
        super(StartDateError, self).__init__(False, AccessError(error_code, developer_message, user_message))


class MilestoneError(AccessResponse):
    """
    Subclasses AccessResponse
    Access denied because the user hasn't completed the needed milestones (pre-reqs/entrance exams).
    """
    def __init__(self):
        error_code = "unfulfilled milestones"
        developer_message = "User has not completed the necessary milestones"
        user_message = "You have uncompleted milestones"
        super(MilestoneError, self).__init__(False, AccessError(error_code, developer_message, user_message))


class VisibilityError(AccessResponse):
    """
    Subclasses AccessResponse
    Access denied because the course is only visible to staff and the user is not staff
    """
    def __init__(self):
        error_code = "visible_to_staff_only"
        developer_message = "Course is only visible to staff and user is not staff"
        user_message = "Course is not visible to you"
        super(VisibilityError, self).__init__(False, AccessError(error_code, developer_message, user_message))


class MobileAvailabilityError(AccessResponse):
    """
    Subclasses AccessResponse
    Access denied because the course is not available on mobile and the user is not a beta tester or staff
    """
    def __init__(self):
        error_code = "mobile_unavailable"
        developer_message = "Course is not available on mobile for this user"
        user_message = "You cannot view this course on mobile"
        super(MobileAvailabilityError, self).__init__(error_code, developer_message, user_message)
