class AccessResponse(object):
    def __init__(self, has_access, access_error):
        self.has_access = has_access
        self.access_error = access_error

    def __nonzero__(self):
        return self.has_access

    def __eq__(self, other):
        return (
            isinstance(other, AccessResponse) and
            self.has_access == other.has_access and
            self.access_error == other.access_error
        )

    def __hash__(self):
        return hash(self.__key())

    def __key(self):
        return self.has_access, self.access_error

    def to_json(self):
        return {
            "has_access": self.has_access,
            "access_error": self.access_error.to_json() if self.access_error is not None else None
        }

class AccessError(object):
    def __init__(self, error_code, developer_message, user_message):
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

    def __key(self):
        return self.error_code, self.developer_message, self.user_message

    def __hash__(self):
        return hash(self.__key())

    def to_json(self):
        return {
            "error_code": self.error_code,
            "developer_message": self.developer_message,
            "user_message": self.user_message
        }

class StartDateError(AccessError):
    """Access denied because the course has not started yet and the user is not staff"""
    def __init__(self, user_message):
        developer_message = "Course does not start until {start} and user does not have staff access".format(start = user_message)
        super(StartDateError, self).__init__("course_not_started", developer_message, user_message)

class MilestoneError(AccessError):
    """Access denied because the user hasn't completed the needed milestones (pre-reqs/entrance exams)."""
    def __init__(self):
        super(MilestoneError, self).__init__("unfulfilled milestones", "User has not completed the necessary milestones", "You have uncompleted milestones")

class VisibilityError(AccessError):
    """Access denied because the course is only visible to staff and the user is not staff"""
    def __init__(self):
        developer_message = "Course is only visible to staff and user is not staff"
        user_message = "Course is not visible to you"
        super(VisibilityError, self).__init__("visible_to_staff_only", developer_message, user_message)

class MobileAvailabilityError(AccessError):
    """Access denied because the course is not available on mobile and the user is not a beta tester or staff"""
    def __init__(self):
        developer_message = "Course is not available on mobile for this user"
        user_message = "You cannot view this course on mobile"
        super(MobileAvailabilityError, self).__init__("mobile_unavailable", developer_message, user_message)