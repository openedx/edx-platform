"""
Permission definitions for the ccx djangoapp
"""

from bridgekeeper import perms
from courseware.rules import HasAccessRule

VIEW_CCX_COACH_DASHBOARD = 'ccx.view_ccx_coach_dashboard'
perms[VIEW_CCX_COACH_DASHBOARD] = HasAccessRule('staff')
