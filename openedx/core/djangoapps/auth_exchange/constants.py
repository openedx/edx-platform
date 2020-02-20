# Use bit-shifting so that scopes can be easily combined and checked.
DEFAULT_SCOPE = 0
OPEN_ID_SCOPE = 1 << 0
PROFILE_SCOPE = 1 << 1
EMAIL_SCOPE = 1 << 2
COURSE_STAFF_SCOPE = 1 << 3
COURSE_INSTRUCTOR_SCOPE = 1 << 4
PERMISSIONS = 1 << 5

# Scope setting as required by django-oauth2-provider
# The default scope value is SCOPES[0][0], which in this case is zero.
# `django-oauth2-provider` considers a scope value of zero as empty,
# ignoring its name when requested.
SCOPES = (
    (DEFAULT_SCOPE, 'default'),
    (OPEN_ID_SCOPE, 'openid'),
    (PROFILE_SCOPE, 'profile'),
    (EMAIL_SCOPE, 'email'),
    (COURSE_STAFF_SCOPE, 'course_staff'),
    (COURSE_INSTRUCTOR_SCOPE, 'course_instructor'),
    (PERMISSIONS, 'permissions')
)

SCOPE_NAMES = [(name, name) for (value, name) in SCOPES]