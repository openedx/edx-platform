"""
Default settings for the password_policy app.
"""


def plugin_settings(settings):
    """
    Adds default settings for the password_policy app.
    """
    # Settings for managing the rollout of password policy compliance enforcement.
    settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG = {
        # Global switch to enable/disable password policy compliance enforcement on login.
        'ENFORCE_COMPLIANCE_ON_LOGIN': False,

        # The date that staff users (users with is_staff permissions) will be required to be compliant with
        # current password policy requirements. After this date, non-compliant users will be forced to reset their
        # password before logging in.
        #
        # This should be a timezone-aware date string parsable by dateutils.parser.parse
        # Ex: 2018-04-19 00:00:00+00:00
        'STAFF_USER_COMPLIANCE_DEADLINE': None,

        # The date that users with elevated privileges (users with entries in the course_access_roles table) will be
        # required to be compliant with current password policy requirements. After this date, non-compliant users will
        # be forced to reset their password before logging in.
        #
        # This should be a timezone-aware date string parsable by dateutils.parser.parse
        # Ex: 2018-04-19 00:00:00+00:00
        'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': None,

        # The date that all users will be required to be compliant with current password policy requirements. After
        # this date, non-compliant users will be forced to reset their password before logging in.
        #
        # This should be a timezone-aware date string parsable by dateutils.parser.parse
        # Ex: 2018-04-19 00:00:00+00:00
        'GENERAL_USER_COMPLIANCE_DEADLINE': None,
    }
