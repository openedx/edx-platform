"""All Error Types pertaining to Enrollment."""


class CourseEnrollmentError(Exception):
    """Generic Course Enrollment Error.

    Describes any error that may occur when reading or updating enrollment information for a user or a course.

    """
    def __init__(self, msg, data=None):
        super(CourseEnrollmentError, self).__init__(msg)
        # Corresponding information to help resolve the error.
        self.data = data


class CourseNotFoundError(CourseEnrollmentError):
    pass


class UserNotFoundError(CourseEnrollmentError):
    pass


class CourseEnrollmentClosedError(CourseEnrollmentError):
    pass


class CourseEnrollmentFullError(CourseEnrollmentError):
    pass


class CourseEnrollmentExistsError(CourseEnrollmentError):
    enrollment = None

    def __init__(self, message, enrollment):
        super(CourseEnrollmentExistsError, self).__init__(message)
        self.enrollment = enrollment


class CourseModeNotFoundError(CourseEnrollmentError):
    """The requested course mode could not be found."""
    pass


class EnrollmentNotFoundError(CourseEnrollmentError):
    """The requested enrollment could not be found."""
    pass


class EnrollmentApiLoadError(CourseEnrollmentError):
    """The data API could not be loaded."""
    pass
