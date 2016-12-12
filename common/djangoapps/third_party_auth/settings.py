"""Settings for the third-party auth module.

The flow for settings registration is:

The base settings file contains a boolean, ENABLE_THIRD_PARTY_AUTH, indicating
whether this module is enabled. startup.py probes the ENABLE_THIRD_PARTY_AUTH.
If true, it:

    a) loads this module.
    b) calls apply_settings(), passing in the Django settings
"""

_FIELDS_STORED_IN_SESSION = ['auth_entry', 'next']
_MIDDLEWARE_CLASSES = (
    'third_party_auth.middleware.ExceptionMiddleware',
)
_SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard'


def apply_settings(django_settings):
    """Set provider-independent settings."""

    # Whitelisted URL query parameters retrained in the pipeline session.
    # Params not in this whitelist will be silently dropped.
    django_settings.FIELDS_STORED_IN_SESSION = _FIELDS_STORED_IN_SESSION

    # Inject exception middleware to make redirects fire.
    django_settings.MIDDLEWARE_CLASSES += _MIDDLEWARE_CLASSES

    # Where to send the user if there's an error during social authentication
    # and we cannot send them to a more specific URL
    # (see middleware.ExceptionMiddleware).
    django_settings.SOCIAL_AUTH_LOGIN_ERROR_URL = '/'

    # Where to send the user once social authentication is successful.
    django_settings.SOCIAL_AUTH_LOGIN_REDIRECT_URL = _SOCIAL_AUTH_LOGIN_REDIRECT_URL

    # Inject our customized auth pipeline. All auth backends must work with
    # this pipeline.
    django_settings.SOCIAL_AUTH_PIPELINE = (
        'third_party_auth.pipeline.parse_query_params',
        'social.pipeline.social_auth.social_details',
        'social.pipeline.social_auth.social_uid',
        'social.pipeline.social_auth.auth_allowed',
        'social.pipeline.social_auth.social_user',
        'third_party_auth.pipeline.associate_by_email_if_login_api',
        'social.pipeline.user.get_username',
        'third_party_auth.pipeline.set_pipeline_timeout',
        'third_party_auth.pipeline.ensure_user_information',
        'social.pipeline.user.create_user',
        'social.pipeline.social_auth.associate_user',
        'third_party_auth.pipeline.create_data_sharing_consent',
        'social.pipeline.social_auth.load_extra_data',
        'social.pipeline.user.user_details',
        'third_party_auth.pipeline.set_logged_in_cookies',
        'third_party_auth.pipeline.login_analytics',
    )

    # Required so that we can use unmodified PSA OAuth2 backends:
    django_settings.SOCIAL_AUTH_STRATEGY = 'third_party_auth.strategy.ConfigurationModelStrategy'

    # We let the user specify their email address during signup.
    django_settings.SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email']

    # Disable exceptions by default for prod so you get redirect behavior
    # instead of a Django error page. During development you may want to
    # enable this when you want to get stack traces rather than redirections.
    django_settings.SOCIAL_AUTH_RAISE_EXCEPTIONS = False

    # Allow users to login using social auth even if their account is not verified yet
    # This is required since we [ab]use django's 'is_active' flag to indicate verified
    # accounts; without this set to True, python-social-auth won't allow us to link the
    # user's account to the third party account during registration (since the user is
    # not verified at that point).
    # We also generally allow unverified third party auth users to login (see the logic
    # in ensure_user_information in pipeline.py) because otherwise users who use social
    # auth to register with an invalid email address can become "stuck".
    # TODO: Remove the following if/when email validation is separated from the is_active flag.
    django_settings.SOCIAL_AUTH_INACTIVE_USER_LOGIN = True
    django_settings.SOCIAL_AUTH_INACTIVE_USER_URL = '/auth/inactive'

    # Context processors required under Django.
    django_settings.SOCIAL_AUTH_UUID_LENGTH = 4
    django_settings.DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
        'social.apps.django_app.context_processors.backends',
        'social.apps.django_app.context_processors.login_redirect',
    )
