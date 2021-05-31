"""
Permission definitions for the theming djangoapp
"""

from bridgekeeper import perms, rules

is_user_active = rules.is_authenticated & rules.is_active
is_global_staff = is_user_active & rules.is_staff

PREVIEW_THEME = 'theming.preview_theme'

perms[PREVIEW_THEME] = is_global_staff
