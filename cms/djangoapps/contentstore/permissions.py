"""
Permission definitions for the contentstore djangoapp.
"""

from bridgekeeper import perms
from lms.djangoapps.courseware.rules import HasAccessRule

EDIT_ACTIVE_CERTIFICATE = 'contentstore.edit_active_certificate'
perms[EDIT_ACTIVE_CERTIFICATE] = HasAccessRule('staff')
