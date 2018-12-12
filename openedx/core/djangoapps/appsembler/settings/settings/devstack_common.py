"""
Settings for Appsembler on devstack, both LMS and CMS.
"""

import dj_database_url
from django.utils.translation import ugettext_lazy as _


def plugin_settings(settings):
    """
    Make devstack lookin shiny blue!
    """
    # TODO: Create a new `common.py` settings instead and move all the common settings to it.
    settings.OAUTH_ENFORCE_SECURE = False

    # disable caching in dev environment
    for cache_key in settings.CACHES.keys():
        settings.CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

    settings.SESSION_ENGINE = 'django.contrib.sessions.backends.db'

    settings.APPSEMBLER_FEATURES = settings.ENV_TOKENS.get('APPSEMBLER_FEATURES', {})

    settings.INSTALLED_APPS += (
        'hijack',
        'compat',
        'hijack_admin',

        'django_extensions',
        'openedx.core.djangoapps.appsembler.sites',
        'openedx.core.djangoapps.appsembler.html_certificates',
        'openedx.core.djangoapps.appsembler.msft_lp',
    )

    # those are usually hardcoded in devstack.py for some reason
    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')
    settings.LMS_ROOT_URL = settings.ENV_TOKENS.get('LMS_ROOT_URL')

    settings.GOOGLE_ANALYTICS_APP_ID = settings.AUTH_TOKENS.get('GOOGLE_ANALYTICS_APP_ID')
    settings.HUBSPOT_API_KEY = settings.AUTH_TOKENS.get('HUBSPOT_API_KEY')
    settings.HUBSPOT_PORTAL_ID = settings.AUTH_TOKENS.get('HUBSPOT_PORTAL_ID')
    settings.MIXPANEL_APP_ID = settings.AUTH_TOKENS.get('MIXPANEL_APP_ID')

    settings.DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
        'openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.google_analytics',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.hubspot',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.mixpanel',
    )

    settings.INTERCOM_APP_ID = settings.AUTH_TOKENS.get("INTERCOM_APP_ID")
    settings.INTERCOM_APP_SECRET = settings.AUTH_TOKENS.get("INTERCOM_APP_SECRET")

    settings.MIDDLEWARE_CLASSES += (
        'organizations.middleware.OrganizationMiddleware',
    )

    settings.SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    if settings.FEATURES.get("ENABLE_TIERS_APP", False):
        settings.TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
        settings.TIERS_EXPIRED_REDIRECT_URL = settings.ENV_TOKENS.get('TIERS_EXPIRED_REDIRECT_URL', None)
        settings.TIERS_ORGANIZATION_TIER_GETTER_NAME = 'get_tier_for_org'

        settings.TIERS_DATABASE_URL = settings.AUTH_TOKENS.get('TIERS_DATABASE_URL')
        settings.DATABASES['tiers'] = dj_database_url.parse(settings.TIERS_DATABASE_URL)
        settings.DATABASE_ROUTERS += ['openedx.core.djangoapps.appsembler.sites.routers.TiersDbRouter']

        settings.MIDDLEWARE_CLASSES += (
            'tiers.middleware.TierMiddleware',
        )

        settings.INSTALLED_APPS += (
            'tiers',
        )

    settings.COURSE_TO_CLONE = "course-v1:Appsembler+CC101+2017"

    settings.CELERY_ALWAYS_EAGER = True

    settings.ALTERNATE_QUEUES = [
        settings.DEFAULT_PRIORITY_QUEUE.replace(settings.QUEUE_VARIANT, alternate + '.')
        for alternate in settings.ALTERNATE_QUEUE_ENVS
    ]

    settings.CELERY_QUEUES.update(
        {
            alternate: {}
            for alternate in settings.ALTERNATE_QUEUES
            if alternate not in settings.CELERY_QUEUES.keys()
        }
    )

    settings.CLONE_COURSE_FOR_NEW_SIGNUPS = False
    settings.HIJACK_ALLOW_GET_REQUESTS = True
    settings.HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

    DEFAULT_COURSE_MODE_SLUG = settings.ENV_TOKENS.get('EDXAPP_DEFAULT_COURSE_MODE_SLUG', 'audit')
    settings.DEFAULT_MODE_NAME_FROM_SLUG = _(DEFAULT_COURSE_MODE_SLUG.capitalize())

    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX = 'custom_domains_redirects'
