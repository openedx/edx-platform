"""
Permission definitions for the contentstore djangoapp
"""

from bridgekeeper import perms, rules

from lms.djangoapps.courseware.rules import HasAccessRule

# Is the user active (and their email verified)?
is_user_active = rules.is_authenticated & rules.is_active
# Is the user global staff?
is_global_staff = is_user_active & rules.is_staff

EDIT_ACTIVE_CERTIFICATE = 'contentstore.edit_active_certificate' 
perms[EDIT_ACTIVE_CERTIFICATE] = is_global_staff
