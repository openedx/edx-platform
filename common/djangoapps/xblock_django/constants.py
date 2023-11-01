"""
Constants used by DjangoXBlockUserService
"""

# Optional attributes stored on the XBlockUser

# The anonymous user ID for the user in the course.
ATTR_KEY_ANONYMOUS_USER_ID = 'edx-platform.anonymous_user_id'
# The global (course-agnostic) anonymous user ID for the user.
ATTR_KEY_DEPRECATED_ANONYMOUS_USER_ID = 'edx-platform.deprecated_anonymous_user_id'
# The country code determined from the user's request IP address.
ATTR_KEY_REQUEST_COUNTRY_CODE = 'edx-platform.request_country_code'
# Whether the user is authenticated or anonymous.
ATTR_KEY_IS_AUTHENTICATED = 'edx-platform.is_authenticated'
# The personally identifiable user ID.
ATTR_KEY_USER_ID = 'edx-platform.user_id'
# The username.
ATTR_KEY_USERNAME = 'edx-platform.username'
# Whether the user is enrolled in the course as a Beta Tester.
ATTR_KEY_USER_IS_BETA_TESTER = 'edx-platform.user_is_beta_tester'
# Whether the user has staff access to the platform.
ATTR_KEY_USER_IS_GLOBAL_STAFF = 'edx-platform.user_is_global_staff'
# Whether the user is a course team member with 'Staff' or 'Admin' access.
ATTR_KEY_USER_IS_STAFF = 'edx-platform.user_is_staff'
# A dict containing user's entries from the `UserPreference` model.
ATTR_KEY_USER_PREFERENCES = 'edx-platform.user_preferences'
# The user's role in the course ('staff', 'instructor', or 'student').
ATTR_KEY_USER_ROLE = 'edx-platform.user_role'
