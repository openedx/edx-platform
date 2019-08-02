"""
Permissions for the instructor dashboard and associated actions
"""

from bridgekeeper import perms
from courseware.rules import HasAccessRule

ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM = 'instructor.allow_student_to_bypass_entrance_exam'
ASSIGN_TO_COHORTS = 'instructor.assign_to_cohorts'
EDIT_COURSE_ACCESS = 'instructor.edit_course_access'
EDIT_FORUM_ROLES = 'instructor.edit_forum_roles'
EDIT_INVOICE_VALIDATION = 'instructor.edit_invoice_validation'
VIEW_ISSUED_CERTIFICATES = 'instructor.view_issued_certificates'


perms[ALLOW_STUDENT_TO_BYPASS_ENTRANCE_EXAM] = HasAccessRule('staff')
perms[ASSIGN_TO_COHORTS] = HasAccessRule('staff')
perms[EDIT_COURSE_ACCESS] = HasAccessRule('instructor')
perms[EDIT_FORUM_ROLES] = HasAccessRule('staff')
perms[EDIT_INVOICE_VALIDATION] = HasAccessRule('staff')
perms[VIEW_ISSUED_CERTIFICATES] = HasAccessRule('staff')
