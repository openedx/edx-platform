"""
Permissions for the instructor dashboard and associated actions
"""

from bridgekeeper import perms
from bridgekeeper.rules import is_staff

from lms.djangoapps.courseware.rules import HasAccessRule, HasRolesRule
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.rules import HasPermissionRule, HasForumsRolesRule
from openedx.core.djangoapps.django_comment_common.models import FORUM_ROLE_ADMINISTRATOR

ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM = 'instructor.allow_student_to_bypass_entrance_exam'
ASSIGN_TO_COHORTS = 'instructor.assign_to_cohorts'
EDIT_COURSE_ACCESS = 'instructor.edit_course_access'
EDIT_FORUM_ROLES = 'instructor.edit_forum_roles'
EDIT_INVOICE_VALIDATION = 'instructor.edit_invoice_validation'
ENABLE_CERTIFICATE_GENERATION = 'instructor.enable_certificate_generation'
GENERATE_CERTIFICATE_EXCEPTIONS = 'instructor.generate_certificate_exceptions'
GENERATE_BULK_CERTIFICATE_EXCEPTIONS = 'instructor.generate_bulk_certificate_exceptions'
GIVE_STUDENT_EXTENSION = 'instructor.give_student_extension'
VIEW_ISSUED_CERTIFICATES = 'instructor.view_issued_certificates'
CAN_RESEARCH = 'instructor.research'
CAN_ENROLL = 'instructor.enroll'
CAN_BETATEST = 'instructor.enroll_beta'
ENROLLMENT_REPORT = 'instructor.enrollment_report'
EXAM_RESULTS = 'instructor.view_exam_results'
OVERRIDE_GRADES = 'instructor.override_grades'
SHOW_TASKS = 'instructor.show_tasks'
VIEW_COUPONS = 'instructor.view_coupons'
EMAIL = 'instructor.email'
RESCORE_EXAMS = 'instructor.rescore_exams'
VIEW_REGISTRATION = 'instructor.view_registration'
VIEW_DASHBOARD = 'instructor.dashboard'
VIEW_ENROLLMENTS = 'instructor.view_enrollments'
VIEW_FORUM_MEMBERS = 'instructor.view_forum_members'
MANAGE_ORAS = 'insructor.manage_oras'
MANAGE_DISCUSSIONS = 'instructor.manage_discussions'
MANAGE_STUDENTS = 'instructor.manage_students'
MANAGE_MEMBERSHIP_LIMITED = 'instructor.manage_membership_limited'
MANAGE_MEMBERSHIP_FULL = 'instructor.manage_membership_full'
MANAGE_COHORTS = 'instructor.manage_cohorts'

perms[ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM] = HasAccessRule('staff')
perms[ASSIGN_TO_COHORTS] = HasAccessRule('staff')
perms[EDIT_COURSE_ACCESS] = HasAccessRule('instructor')
perms[EDIT_FORUM_ROLES] = HasAccessRule('staff')
perms[EDIT_INVOICE_VALIDATION] = HasAccessRule('staff')
perms[ENABLE_CERTIFICATE_GENERATION] = is_staff
perms[GENERATE_CERTIFICATE_EXCEPTIONS] = is_staff
perms[GENERATE_BULK_CERTIFICATE_EXCEPTIONS] = is_staff
perms[GIVE_STUDENT_EXTENSION] = HasAccessRule('staff')
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[VIEW_ISSUED_CERTIFICATES] = (
    HasAccessRule('staff') |
    HasRolesRule('data_researcher') |
    HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
# only global staff or those with the data_researcher role can access the data download tab
# HasAccessRule('staff') also includes course staff
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[CAN_RESEARCH] = (
    is_staff |
    HasRolesRule('data_researcher') |
    HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
perms[CAN_ENROLL] = HasAccessRule('staff')
perms[CAN_BETATEST] = HasAccessRule('instructor')
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[ENROLLMENT_REPORT] = (
    HasAccessRule('staff') |
    HasRolesRule('data_researcher') |
    HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[VIEW_COUPONS] = (
    HasAccessRule('staff') |
    HasRolesRule('data_researcher') |
    HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS)
)
perms[EXAM_RESULTS] = HasAccessRule('staff')
perms[OVERRIDE_GRADES] = HasAccessRule('staff')
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[SHOW_TASKS] = (
    HasAccessRule('staff') |
    HasRolesRule('data_researcher') | (
        HasPermissionRule(CourseRolesPermission.MANAGE_STUDENTS) &
        HasPermissionRule(CourseRolesPermission.ACCESS_DATA_DOWNLOADS) &
        HasPermissionRule(CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD)
    )
)
perms[EMAIL] = HasAccessRule('staff')
perms[RESCORE_EXAMS] = HasAccessRule('instructor')
perms[VIEW_REGISTRATION] = HasAccessRule('staff')
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[VIEW_DASHBOARD] = (
    HasRolesRule('staff', 'instructor', 'data_researcher') |
    HasAccessRule('staff') |
    HasAccessRule('instructor') |
    HasPermissionRule(CourseRolesPermission.ACCESS_INSTRUCTOR_DASHBOARD)
)
perms[VIEW_ENROLLMENTS] = HasAccessRule('staff')
perms[VIEW_FORUM_MEMBERS] = HasAccessRule('staff')
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_ORAS] = (
    HasAccessRule('instructor') |
    HasAccessRule('staff') |
    HasPermissionRule(CourseRolesPermission.MANAGE_GRADES)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_DISCUSSIONS] = (
    HasPermissionRule(CourseRolesPermission.MANAGE_DISCUSSION_MODERATORS) |
    HasForumsRolesRule(FORUM_ROLE_ADMINISTRATOR)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_STUDENTS] = (
    HasAccessRule('instructor') |
    HasAccessRule('staff') |
    HasPermissionRule(CourseRolesPermission.MANAGE_STUDENTS)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_MEMBERSHIP_LIMITED] = (
    HasAccessRule('staff') |
    HasPermissionRule(CourseRolesPermission.MANAGE_USERS_EXCEPT_ADMIN_AND_STAFF)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_MEMBERSHIP_FULL] = (
    HasAccessRule('instructor') |
    HasPermissionRule(CourseRolesPermission.MANAGE_ALL_USERS)
)
# TODO: remove role checks once course_roles is fully implemented and data is migrated
perms[MANAGE_COHORTS] = (
    HasAccessRule('instructor') |
    HasAccessRule('staff') |
    HasPermissionRule(CourseRolesPermission.MANAGE_COHORTS)
)
