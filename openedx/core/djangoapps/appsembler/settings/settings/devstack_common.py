"""
Settings for Appsembler on devstack, both LMS and CMS.
"""

import sys


def plugin_settings(settings):
    """
    Appsembler overrides devstack, both LMS and CMS.

    This runs after `production_common.py`, check that for relevant settings.
    """
    settings.OAUTH_ENFORCE_SECURE = False
    settings.SESSION_ENGINE = 'django.contrib.sessions.backends.db'

    if not settings.AMC_APP_URL:
        settings.AMC_APP_URL = 'http://localhost:13000'

    if not settings.AMC_APP_OAUTH2_CLIENT_ID:
        settings.AMC_APP_OAUTH2_CLIENT_ID = 'dev-amc-app-oauth2-client-id'

    # Disable caching in dev environment
    if not settings.FEATURES.get('ENABLE_DEVSTACK_CACHES', False):
        print('\nAppsembler: disabling devstack caches\n', file=sys.stderr)
        for cache_key in list(settings.CACHES.keys()):
            if cache_key != 'celery':  # NOTE: Disabling cache breaks things like Celery subtasks
                settings.CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

    settings.INSTALLED_APPS += (
        'django_extensions',
    )

    # Those are usually hardcoded in devstack.py for some reason
    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')
    settings.LMS_ROOT_URL = settings.ENV_TOKENS.get('LMS_ROOT_URL')
    settings.FEATURES['ENABLE_CREATOR_GROUP'] = settings.ENV_TOKENS['FEATURES'].get('ENABLE_CREATOR_GROUP', False)

    settings.COURSE_TO_CLONE = "course-v1:Appsembler+CC101+2017"

    settings.CELERY_ALWAYS_EAGER = True

    settings.ALTERNATE_QUEUES = [
        settings.DEFAULT_PRIORITY_QUEUE.replace(settings.QUEUE_VARIANT, alternate + '.')
        for alternate in settings.ALTERNATE_QUEUE_ENVS
    ]

    settings.CELERY_QUEUES.update({
        alternate: {}
        for alternate in settings.ALTERNATE_QUEUES
        if alternate not in settings.CELERY_QUEUES.keys()
    })
