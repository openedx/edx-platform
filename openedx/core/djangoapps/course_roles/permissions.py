"""
Bridgekeeper permissions for course roles
"""

from bridgekeeper import perms
from bridgekeeper.rules import is_staff

from lms.djangoapps.courseware.rules import HasRolesRule
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.rules import HasPermissionRule, HasForumsRolesRule


# DO NOT USE FOR AUTHORIZATION
# This is added to ensure is_staff users can access the admin dashboard and is
# NOT intended for code authorization checks
# TODO: Consider removing this in favor of overriding the query method
perms['course_roles.is_staff'] = (
    is_staff
)
perms[CourseRolesPermission.MANAGE_CONTENT.perm_name] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_CONTENT)
)
perms[CourseRolesPermission.MANAGE_COURSE_SETTINGS.perm_name] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COURSE_SETTINGS)
)
perms[CourseRolesPermission.MANAGE_ADVANCED_SETTINGS.perm_name] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ADVANCED_SETTINGS)
)
perms[CourseRolesPermission.VIEW_ALL_CONTENT.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_ALL_CONTENT)
)
perms[CourseRolesPermission.VIEW_LIVE_PUBLISHED_CONTENT.perm_name] = (
    HasRolesRule('beta_testers', 'ccx_coach')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.VIEW_LIVE_PUBLISHED_CONTENT)
)
perms[CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.perm_name] = (
    HasPermissionRule(CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT)
)
perms[CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD.perm_name] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'data_researcher', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD)
)
perms[CourseRolesPermission.ACCESS_DATA_DOWNLOADS.perm_name] = (
    HasRolesRule('data_researcher')
    | HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
perms[CourseRolesPermission.MANAGE_GRADES.perm_name] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_GRADES)
)
perms[CourseRolesPermission.VIEW_GRADEBOOK.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_GRADEBOOK)
)
perms[CourseRolesPermission.MANAGE_ALL_USERS.perm_name] = (
    HasRolesRule('instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ALL_USERS)
)
perms[CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF.perm_name] = (
    HasRolesRule('staff', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF)
)
perms[CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS)
)
perms[CourseRolesPermission.MANAGE_COHORTS.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COHORTS)
)
perms[CourseRolesPermission.MANAGE_STUDENTS.perm_name] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_STUDENTS)
)
perms[CourseRolesPermission.MODERATE_DISCUSSION_FORUMS.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS)
)
perms[CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'group_moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT)
)
perms[CourseRolesPermission.MANAGE_CERTIFICATES.perm_name] = (
    HasPermissionRule(CourseRolesPermission.MANAGE_CERTIFICATES)
)
perms[CourseRolesPermission.MANAGE_LIBRARIES.perm_name] = (
    HasRolesRule('library_user')
    | HasPermissionRule(CourseRolesPermission.MANAGE_LIBRARIES)
)
perms[CourseRolesPermission.GENERAL_MASQUERADING.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.GENERAL_MASQUERADING)
)
perms[CourseRolesPermission.SPECIFIC_MASQUERADING.perm_name] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.SPECIFIC_MASQUERADING)
)
