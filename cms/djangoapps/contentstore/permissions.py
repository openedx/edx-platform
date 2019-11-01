"""
Permission definitions for the contentstore djangoapp
"""

from bridgekeeper import perms
from .rules import HasAccessRule

EDIT_ENROLLMENT_END = 'contentstore.edit_enrollment_end'

perms[EDIT_ENROLLMENT_END] = HasAccessRule('staff')
