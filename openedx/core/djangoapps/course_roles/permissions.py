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
perms[f'course_roles.{CourseRolesPermission.MANAGE_CONTENT.value.name}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_CONTENT)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_COURSE_SETTINGS.value.name}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COURSE_SETTINGS)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_ADVANCED_SETTINGS.value.name}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ADVANCED_SETTINGS)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_ALL_CONTENT.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_ALL_CONTENT)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_LIVE_PUBLISHED_CONTENT.value.name}'] = (
    HasRolesRule('beta_testers', 'ccx_coach')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.VIEW_LIVE_PUBLISHED_CONTENT)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.value.name}'] = (
    HasPermissionRule(CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT)
)
perms[f'course_roles.{CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'data_researcher', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD)
)
perms[f'course_roles.{CourseRolesPermission.ACCESS_DATA_DOWNLOADS.value.name}'] = (
    HasRolesRule('data_researcher')
    | HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_GRADES.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_GRADES)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_GRADEBOOK.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_GRADEBOOK)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_ALL_USERS.value.name}'] = (
    HasRolesRule('instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ALL_USERS)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF.value.name}'] = (
    HasRolesRule('staff', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_COHORTS.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COHORTS)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_STUDENTS.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_STUDENTS)
)
perms[f'course_roles.{CourseRolesPermission.MODERATE_DISCUSSION_FORUMS.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS)
)
perms[f'course_roles.{CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'group_moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_CERTIFICATES.value.name}'] = (
    HasPermissionRule(CourseRolesPermission.MANAGE_CERTIFICATES)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_LIBRARIES.value.name}'] = (
    HasRolesRule('library_user')
    | HasPermissionRule(CourseRolesPermission.MANAGE_LIBRARIES)
)
perms[f'course_roles.{CourseRolesPermission.GENERAL_MASQUERADING.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.GENERAL_MASQUERADING)
)
perms[f'course_roles.{CourseRolesPermission.SPECIFIC_MASQUERADING.value.name}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.SPECIFIC_MASQUERADING)
)
