"""
Bridgekeeper permissions for course roles
"""

from bridgekeeper import perms

from lms.djangoapps.courseware.rules import HasRolesRule
from openedx.core.djangoapps.course_roles.permissions import CourseRolesPermission
from openedx.core.djangoapps.course_roles.rules import HasPermissionRule, HasForumsRolesRule


perms[f'course_roles.{CourseRolesPermission.MANAGE_CONTENT.value}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_CONTENT.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_COURSE_SETTINGS.value}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COURSE_SETTINGS.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_ADVANCED_SETTINGS.value}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ADVANCED_SETTINGS.value)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_ALL_CONTENT.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_ALL_CONTENT.value)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_ONLY_LIVE_PUBLISHED_CONTENT.value}'] = (
    HasRolesRule('beta_testers', 'ccx_coach')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.VIEW_ONLY_LIVE_PUBLISHED_CONTENT.value)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.value}'] = (
    HasPermissionRule(CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.value)
)
perms[f'course_roles.{CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD.value}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'data_researcher', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD.value)
)
perms[f'course_roles.{CourseRolesPermission.ACCESS_DATA_DOWNLOADS.value}'] = (
    HasRolesRule('data_researcher')
    | HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_GRADES.value}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_GRADES.value)
)
perms[f'course_roles.{CourseRolesPermission.VIEW_GRADEBOOK.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.VIEW_GRADEBOOK.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_ALL_USERS.value}'] = (
    HasRolesRule('instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_ALL_USERS.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF.value}'] = (
    HasRolesRule('staff', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator')
    | HasPermissionRule(CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_COHORTS.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_COHORTS.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_STUDENTS.value}'] = (
    HasRolesRule('staff', 'instructor', 'ccx_coach', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.MANAGE_STUDENTS.value)
)
perms[f'course_roles.{CourseRolesPermission.MODERATE_DISCUSSION_FORUMS.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS.value)
)
perms[f'course_roles.{CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasForumsRolesRule('administrator', 'moderator', 'group_moderator', 'community_ta')
    | HasPermissionRule(CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_CERTIFICATES.value}'] = (
    HasPermissionRule(CourseRolesPermission.MANAGE_CERTIFICATES.value)
)
perms[f'course_roles.{CourseRolesPermission.MANAGE_LIBRARIES.value}'] = (
    HasRolesRule('library_user')
    | HasPermissionRule(CourseRolesPermission.MANAGE_LIBRARIES.value)
)
perms[f'course_roles.{CourseRolesPermission.GENERAL_MASQUERADING.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.GENERAL_MASQUERADING.value)
)
perms[f'course_roles.{CourseRolesPermission.SPECIFIC_MASQUERADING.value}'] = (
    HasRolesRule('staff', 'instructor', 'limited_staff')
    | HasPermissionRule(CourseRolesPermission.SPECIFIC_MASQUERADING.value)
)
