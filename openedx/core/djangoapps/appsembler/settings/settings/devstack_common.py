"""
Settings for Appsembler on devstack, both LMS and CMS.
"""


def plugin_settings(settings):
    """
    Appsembler overrides devstack, both LMS and CMS.

    This runs after `aws_common.py`, check that for relevant settings.
    """
    settings.OAUTH_ENFORCE_SECURE = False
    settings.SESSION_ENGINE = 'django.contrib.sessions.backends.db'

    # disable caching in dev environment
    for cache_key in settings.CACHES.keys():
        settings.CACHES[cache_key]['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

    settings.INSTALLED_APPS += (
        'django_extensions',
    )

    # Those are usually hardcoded in devstack.py for some reason
    settings.LMS_BASE = settings.ENV_TOKENS.get('LMS_BASE')
    settings.LMS_ROOT_URL = settings.ENV_TOKENS.get('LMS_ROOT_URL')

    settings.MIDDLEWARE_CLASSES += (
        'organizations.middleware.OrganizationMiddleware',
    )

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
