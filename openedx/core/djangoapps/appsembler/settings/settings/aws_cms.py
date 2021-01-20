"""
Settings for Appsembler on CMS in Production (aka AWS).
"""

from openedx.core.djangoapps.appsembler.settings.settings import aws_common


def plugin_settings(settings):
    """
    Appsembler CMS overrides for both production AND devstack.

    Make sure those are compatible for devstack via defensive coding.

    This file, however, won't run in test environments.
    """
    aws_common.plugin_settings(settings)

    settings.APPSEMBLER_SECRET_KEY = settings.AUTH_TOKENS.get("APPSEMBLER_SECRET_KEY")

    settings.INTERCOM_APP_ID = settings.AUTH_TOKENS.get("INTERCOM_APP_ID")
    settings.INTERCOM_APP_SECRET = settings.AUTH_TOKENS.get("INTERCOM_APP_SECRET")

    settings.FEATURES['ENABLE_COURSEWARE_INDEX'] = True
    settings.FEATURES['ENABLE_LIBRARY_INDEX'] = True

    settings.ELASTIC_FIELD_MAPPINGS = {
        "start_date": {
            "type": "date"
        }
    }

    if settings.SENTRY_DSN:
        settings.RAVEN_CONFIG['tags']['app'] = 'cms'

    settings.MIDDLEWARE_CLASSES += (
        # TODO: OrganizationMiddleware should be added before Tiers middleware in `aws_common.plugin_settings()`
        'organizations.middleware.OrganizationMiddleware',
    )

    settings.SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5
