"""
Permissions for the instructor dashboard and associated actions
"""

from bridgekeeper import perms
from courseware.rules import HasAccessRule


VIEW_ISSUED_CERTIFICATES = 'instructor.view_issued_certificates'


perms[VIEW_ISSUED_CERTIFICATES] = HasAccessRule('staff')
