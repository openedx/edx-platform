'''
Formerly models.py was a single module. Now two to accommodate treating course enrollment differently, for SOX
compliance purposes.
'''
from .course_enrollment import (
    CourseEnrollment,
    CourseEnrollmentAllowed
)
from .student import *
