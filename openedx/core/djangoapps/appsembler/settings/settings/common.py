"""
Common Appsembler settings for all environments in both LMS and CMS.
"""


def plugin_settings(settings):
    """
    Appsembler overrides for all of the environments (devstack, prod and test) in both of CMS and LMS.

    This is a useful place for placing Appsembler-wide settings, for production
    and devstack settings checkout the other `common_aws.py` and `common_devstack.py` sibling files.
    """
    settings.APPSEMBLER_FEATURES = {}

    settings.INSTALLED_APPS += (
        'hijack',
        'compat',
        'hijack_admin',

        'openedx.core.djangoapps.appsembler.sites',
        'openedx.core.djangoapps.appsembler.html_certificates',
        'openedx.core.djangoapps.appsembler.api',
    )

    settings.DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
        'openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.google_analytics',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.hubspot',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.mixpanel',
    )

    settings.SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    settings.CLONE_COURSE_FOR_NEW_SIGNUPS = False
    settings.HIJACK_ALLOW_GET_REQUESTS = True
    settings.HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX = 'custom_domains_redirects'

    settings.COPY_SEGMENT_EVENT_PROPERTIES_TO_TOP_LEVEL = True
