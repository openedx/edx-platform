"""
Permission definitions for the enrollments djangoapp
"""

from bridgekeeper import perms, rules
from lms.djangoapps.courseware.rules import HasAccessRule

is_user_active = rules.is_authenticated & rules.is_active
is_global_staff = is_user_active & rules.is_staff

ENROLL_IN_COURSE = 'enrollment.enroll_in_course'
VIEW_ENROLLMENT_DATA = 'enrollment.view_enrollment_data'
CREATE_ENROLLMENT = 'enrollment.create_enrollment'
DEACTIVATE_ENROLLMENT = 'enrollment.deactivate_enrollment'

perms[ENROLL_IN_COURSE] = HasAccessRule('enroll')
perms[VIEW_ENROLLMENT_DATA] = is_global_staff
perms[CREATE_ENROLLMENT] = is_global_staff
perms[DEACTIVATE_ENROLLMENT] = is_global_staff
