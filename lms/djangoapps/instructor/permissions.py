"""
Permissions for the instructor dashboard and associated actions
"""
from bridgekeeper import perms
from bridgekeeper.rules import is_staff
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import BasePermission

from lms.djangoapps.courseware.rules import HasAccessRule, HasRolesRule
from openedx.core.lib.courses import get_course_by_id

ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM = 'instructor.allow_student_to_bypass_entrance_exam'
ASSIGN_TO_COHORTS = 'instructor.assign_to_cohorts'
EDIT_COURSE_ACCESS = 'instructor.edit_course_access'
EDIT_FORUM_ROLES = 'instructor.edit_forum_roles'
EDIT_INVOICE_VALIDATION = 'instructor.edit_invoice_validation'
ENABLE_CERTIFICATE_GENERATION = 'instructor.enable_certificate_generation'
GENERATE_CERTIFICATE_EXCEPTIONS = 'instructor.generate_certificate_exceptions'
GENERATE_BULK_CERTIFICATE_EXCEPTIONS = 'instructor.generate_bulk_certificate_exceptions'
START_CERTIFICATE_GENERATION = 'instructor.start_certificate_generation'
START_CERTIFICATE_REGENERATION = 'instructor.start_certificate_regeneration'
CERTIFICATE_EXCEPTION_VIEW = 'instructor.certificate_exception_view'
CERTIFICATE_INVALIDATION_VIEW = 'instructor.certificate_invalidation_view'
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


perms[ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM] = HasAccessRule('staff')
perms[ASSIGN_TO_COHORTS] = HasAccessRule('staff')
perms[EDIT_COURSE_ACCESS] = HasAccessRule('instructor')
perms[EDIT_FORUM_ROLES] = HasAccessRule('staff')
perms[EDIT_INVOICE_VALIDATION] = HasAccessRule('staff')
perms[ENABLE_CERTIFICATE_GENERATION] = is_staff | HasAccessRule('instructor')
perms[GENERATE_CERTIFICATE_EXCEPTIONS] = is_staff | HasAccessRule('instructor')
perms[GENERATE_BULK_CERTIFICATE_EXCEPTIONS] = is_staff | HasAccessRule('instructor')
perms[START_CERTIFICATE_GENERATION] = is_staff | HasAccessRule('instructor')
perms[START_CERTIFICATE_REGENERATION] = is_staff | HasAccessRule('instructor')
perms[CERTIFICATE_EXCEPTION_VIEW] = is_staff | HasAccessRule('instructor')
perms[CERTIFICATE_INVALIDATION_VIEW] = is_staff | HasAccessRule('instructor')
perms[GIVE_STUDENT_EXTENSION] = HasAccessRule('staff')
perms[VIEW_ISSUED_CERTIFICATES] = HasAccessRule('staff') | HasRolesRule('data_researcher')
# only global staff or those with the data_researcher role can access the data download tab
# HasAccessRule('staff') also includes course staff
perms[CAN_RESEARCH] = is_staff | HasRolesRule('data_researcher')
perms[CAN_ENROLL] = HasAccessRule('staff')
perms[CAN_BETATEST] = HasAccessRule('instructor')
perms[ENROLLMENT_REPORT] = HasAccessRule('staff') | HasRolesRule('data_researcher')
perms[VIEW_COUPONS] = HasAccessRule('staff') | HasRolesRule('data_researcher')
perms[EXAM_RESULTS] = HasAccessRule('staff')
perms[OVERRIDE_GRADES] = HasAccessRule('staff')
perms[SHOW_TASKS] = HasAccessRule('staff') | HasRolesRule('data_researcher')
perms[EMAIL] = HasAccessRule('staff')
perms[RESCORE_EXAMS] = HasAccessRule('instructor')
perms[VIEW_REGISTRATION] = HasAccessRule('staff')
perms[VIEW_DASHBOARD] = \
    HasRolesRule(
        'staff',
        'instructor',
        'data_researcher'
) | HasAccessRule('staff') | HasAccessRule('instructor')
perms[VIEW_ENROLLMENTS] = HasAccessRule('staff')
perms[VIEW_FORUM_MEMBERS] = HasAccessRule('staff')


class InstructorPermission(BasePermission):
    """Generic permissions"""
    def has_permission(self, request, view):
        course = get_course_by_id(CourseKey.from_string(view.kwargs.get('course_id')))
        permission = getattr(view, 'permission_name', None)
        return request.user.has_perm(permission, course)
