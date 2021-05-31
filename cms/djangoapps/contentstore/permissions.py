"""
Permission definitions for the contentstore djangoapp
"""

from bridgekeeper import perms, rules
from common.djangoapps.student.roles import CourseCreatorRole
from lms.djangoapps.courseware.rules import HasRolesRule

is_user_active = rules.is_authenticated & rules.is_active
is_global_staff = is_user_active & rules.is_staff

EDIT_ACTIVE_CERTIFICATE = 'contentstore.edit_active_certificate'
DELETE_ACTIVE_CERTIFICATE = 'contentstore.delete_active_certificate'
REINDEX_COURSE = 'contentstore.reindex_course'
RERUN_COURSE = 'contentstore.rerun_course'
ACCESS_COURSE = 'contentstore.access_course'
EDIT_COURSE = 'contentstore.edit_course'
OPTIMIZE_COURSE_LIST = 'contentstore.optimize_course_list'
VIEW_CERTIFICATES_LIST_PAGE = 'contentstore.view_certificates_list_page'
RERUN_CREATOR_STATUS = 'contentstore.rerun_creator_status'

perms[EDIT_ACTIVE_CERTIFICATE] = is_global_staff
perms[DELETE_ACTIVE_CERTIFICATE] = is_global_staff
perms[REINDEX_COURSE] = is_global_staff
perms[RERUN_COURSE] = is_global_staff
perms[ACCESS_COURSE] = is_global_staff
perms[EDIT_COURSE] = is_global_staff
perms[OPTIMIZE_COURSE_LIST] = is_global_staff
perms[VIEW_CERTIFICATES_LIST_PAGE] = is_global_staff
perms[RERUN_CREATOR_STATUS] = is_global_staff
