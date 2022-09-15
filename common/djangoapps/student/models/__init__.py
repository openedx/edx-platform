'''
Formerly models.py was a single module. Now two to accommodate treating course enrollment differently, for SOX
compliance purposes.
'''
from .course_enrollment import (
    CourseEnrollment,
    CourseEnrollmentAllowed,
    EnrollStatusChange,
    CourseEnrollmentException,
    NonExistentCourseError,
    EnrollmentClosedError,
    CourseFullError,
    AlreadyEnrolledError,
    EnrollmentNotAllowed,
    UnenrollmentNotAllowed,
    EnrollmentRefundConfiguration,
    EVENT_NAME_ENROLLMENT_ACTIVATED,
    EVENT_NAME_ENROLLMENT_DEACTIVATED,
    EVENT_NAME_ENROLLMENT_MODE_CHANGED,
    SCORE_RECALCULATION_DELAY_ON_ENROLLMENT_UPDATE
)
from .student import *
