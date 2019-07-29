"""
Permission definitions for the content_type_gating djangoapp
"""

from bridgekeeper import perms
from lms.djangoapps.courseware.rules import HasStaffRolesRule

CONTENT_TYPE_GATING_BYPASS_FBE = 'content_type_gating.bypass_fbe'
perms[CONTENT_TYPE_GATING_BYPASS_FBE] = HasStaffRolesRule()
