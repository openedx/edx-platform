"""
Permission definitions for the course_duration_limits djangoapp
"""

from bridgekeeper import perms
from lms.djangoapps.courseware.rules import HasStaffRolesRule

COURSE_DURATION_LIMITS_BYPASS_FBE = 'course_duration_limits.bypass_fbe'
perms[COURSE_DURATION_LIMITS_BYPASS_FBE] = HasStaffRolesRule()
