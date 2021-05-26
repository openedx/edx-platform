"""
Permission definitions for the contentstore djangoapp
"""

from bridgekeeper import perms, rules
from common.djangoapps.student.roles import CourseCreatorRole
from lms.djangoapps.courseware.rules import HasRolesRule

# Is the user active (and their email verified)?
is_user_active = rules.is_authenticated & rules.is_active
# Is the user global staff?
is_global_staff = is_user_active & rules.is_staff

EDIT_ACTIVE_CERTIFICATE = 'contentstore.edit_active_certificate'
DELETE_ACTIVE_CERTIFICATE = 'contentstore.delete_active_certificate'
REINDEX_COURSE = 'contentstore.reindex_course'
RERUN_COURSE = 'contentstore.rerun_course'
CREATE_COURSE = 'contentstore.create_course'

perms[EDIT_ACTIVE_CERTIFICATE] = is_global_staff
perms[DELETE_ACTIVE_CERTIFICATE] = is_global_staff
perms[REINDEX_COURSE] = is_global_staff
perms[RERUN_COURSE] = is_global_staff
perms[CREATE_COURSE] = HasRolesRule(CourseCreatorRole())
