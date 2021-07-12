"""
Settings for Appsembler on CMS in Production.
"""

import sentry_sdk

from openedx.core.djangoapps.appsembler.settings.settings import production_common


def plugin_settings(settings):
    """
    Appsembler CMS overrides for both production AND devstack.

    Make sure those are compatible for devstack via defensive coding.

    This file, however, won't run in test environments.
    """
    production_common.plugin_settings(settings)

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
        sentry_sdk.set_tag('app', 'cms')

    settings.SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5

    settings.HIJACK_LOGIN_REDIRECT_URL = '/home'
