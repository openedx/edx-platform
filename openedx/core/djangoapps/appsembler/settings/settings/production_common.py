"""
Settings for Appsembler on production in both LMS and CMS.
"""

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


from django.utils.translation import ugettext_lazy as _


def plugin_settings(settings):
    """
    Appsembler overrides for both production AND devstack.

    Make sure those are compatible for devstack via defensive coding.

    This file, however, won't run in test environments.
    """
    settings.APPSEMBLER_FEATURES = settings.ENV_TOKENS.get('APPSEMBLER_FEATURES', settings.APPSEMBLER_FEATURES)
    settings.APPSEMBLER_AMC_API_BASE = settings.AUTH_TOKENS.get('APPSEMBLER_AMC_API_BASE')
    settings.APPSEMBLER_FIRST_LOGIN_API = '/logged_into_edx'

    # Tahoe: RED-1909 - Credentials should be disabled on all sites.
    settings.FEATURES['TAHOE_ENABLE_CREDENTIALS'] = False

    settings.AMC_APP_URL = settings.ENV_TOKENS.get('AMC_APP_URL')
    settings.AMC_APP_OAUTH2_CLIENT_ID = settings.ENV_TOKENS.get('AMC_APP_OAUTH2_CLIENT_ID')

    settings.DEFAULT_COURSE_MODE_SLUG = settings.ENV_TOKENS.get('EDXAPP_DEFAULT_COURSE_MODE_SLUG', 'audit')
    settings.DEFAULT_MODE_NAME_FROM_SLUG = _(settings.DEFAULT_COURSE_MODE_SLUG.capitalize())

    settings.SEARCH_ENGINE = "search.elastic.ElasticSearchEngine"

    settings.INTERCOM_APP_ID = settings.AUTH_TOKENS.get("INTERCOM_APP_ID")
    settings.INTERCOM_APP_SECRET = settings.AUTH_TOKENS.get("INTERCOM_APP_SECRET")

    settings.GOOGLE_ANALYTICS_APP_ID = settings.AUTH_TOKENS.get('GOOGLE_ANALYTICS_APP_ID')
    settings.HUBSPOT_API_KEY = settings.AUTH_TOKENS.get('HUBSPOT_API_KEY')
    settings.HUBSPOT_PORTAL_ID = settings.AUTH_TOKENS.get('HUBSPOT_PORTAL_ID')
    settings.MIXPANEL_APP_ID = settings.AUTH_TOKENS.get('MIXPANEL_APP_ID')

    settings.MANDRILL_API_KEY = settings.AUTH_TOKENS.get("MANDRILL_API_KEY")
    if settings.MANDRILL_API_KEY:
        settings.EMAIL_BACKEND = settings.ENV_TOKENS['EMAIL_BACKEND']
        settings.ANYMAIL = {
            "MANDRILL_API_KEY": settings.MANDRILL_API_KEY,
        }
        settings.INSTALLED_APPS += ['anymail']

    # Sentry
    settings.SENTRY_DSN = settings.AUTH_TOKENS.get('SENTRY_DSN', False)
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[DjangoIntegration()],
            send_default_pii=True,
            environment=settings.FEATURES['ENVIRONMENT'],
        )
        sentry_sdk.set_tag('app', 'edxapp')

    if settings.FEATURES.get('ENABLE_TIERS_APP', False):
        settings.TIERS_ORGANIZATION_MODEL = 'organizations.Organization'
        settings.TIERS_EXPIRED_REDIRECT_URL = settings.ENV_TOKENS.get('TIERS_EXPIRED_REDIRECT_URL', None)

        settings.TIERS_DATABASE_URL = settings.AUTH_TOKENS.get('TIERS_DATABASE_URL')
        settings.DATABASES['tiers'] = dj_database_url.parse(settings.TIERS_DATABASE_URL, ssl_require=True)
        settings.DATABASE_ROUTERS.insert(0, 'openedx.core.djangoapps.appsembler.tahoe_tiers.db_routers.TiersDbRouter')

        settings.MIDDLEWARE += [
            'openedx.core.djangoapps.appsembler.tahoe_tiers.middleware.TahoeTierMiddleware',
        ]
        settings.INSTALLED_APPS += [
            'tiers',
        ]

    if settings.FEATURES.get('APPSEMBLER_MULTI_TENANT_EMAILS', False):
        settings.INSTALLED_APPS += [
            'openedx.core.djangoapps.appsembler.multi_tenant_emails',
        ]

    # On by default on production. See the `site_configuration.tahoe_organization_helpers.py` module.
    settings.FEATURES['TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT'] = settings.ENV_TOKENS['FEATURES'].get(
        'TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT', True
    )

    settings.TAHOE_DEFAULT_COURSE_NAME = settings.ENV_TOKENS.get('TAHOE_DEFAULT_COURSE_NAME', '')
    settings.TAHOE_DEFAULT_COURSE_GITHUB_ORG = settings.ENV_TOKENS.get('TAHOE_DEFAULT_COURSE_GITHUB_ORG', '')
    settings.TAHOE_DEFAULT_COURSE_GITHUB_NAME = settings.ENV_TOKENS.get('TAHOE_DEFAULT_COURSE_GITHUB_NAME', '')
    settings.TAHOE_DEFAULT_COURSE_VERSION = settings.ENV_TOKENS.get('TAHOE_DEFAULT_COURSE_VERSION', '')
    settings.TAHOE_DEFAULT_COURSE_CMS_TASK_DELAY = int(settings.ENV_TOKENS.get(
        'TAHOE_DEFAULT_COURSE_CMS_TASK_DELAY', 0
    ))
    settings.CMS_UPDATE_SEARCH_INDEX_JOB_QUEUE = settings.ENV_TOKENS.get(
        'CMS_UPDATE_SEARCH_INDEX_JOB_QUEUE', 'edx.cms.core.default'
    )

    # force S3 v4 (temporary until we can upgrade to django-storages 1.9)
    settings.S3_USE_SIGV4 = True

    # for some buckets like London ones, we need these non documented django-storages vars
    # https://github.com/jschneier/django-storages/issues/28#issuecomment-265876674
    settings.AWS_S3_REGION_NAME = settings.ENV_TOKENS.get('AWS_S3_REGION_NAME', '')
    settings.AWS_S3_SIGNATURE_VERSION = 's3v4'

    # Honeycomb
    settings.HONEYCOMB_DATASET = settings.AUTH_TOKENS.get('HONEYCOMB_DATASET', None)
    settings.HONEYCOMB_WRITEKEY = settings.AUTH_TOKENS.get('HONEYCOMB_WRITEKEY', None)

    settings.TAHOE_SCORM_XBLOCK_ROOT_DIR = settings.ENV_TOKENS.get('TAHOE_SCORM_XBLOCK_ROOT_DIR', False)

    # DEPRECATE starting with Lilac release: unnecessary
    # All installed XBlocks need to be listed here whether they require
    # learner interaction or not.  Otherwise, course outline will
    # show subsection, section, and course as incomplete.
    settings.TAHOE_COURSE_OUTLINE_COMPLETABLE_BLOCK_TYPES = settings.ENV_TOKENS.get(
        'TAHOE_COURSE_OUTLINE_COMPLETABLE_BLOCK_TYPES', []
    )

    settings.CELERY_ROUTES = (
        settings.CELERY_ROUTES,
        {
            'lms.djangoapps.grades.tasks.recalculate_subsection_grade_v3': {
                'queue': settings.ENV_TOKENS.get('RECALCULATE_GRADES_ROUTING_KEY', settings.DEFAULT_PRIORITY_QUEUE),
                'routing_key': settings.ENV_TOKENS.get('RECALCULATE_GRADES_ROUTING_KEY', settings.DEFAULT_PRIORITY_QUEUE)
            }
        }
    )

    # add a cache for user profile metadata for use by the TahoeUserMetadataProcessor
    # must be done here as lms/envs/production sets via ENV_TOKENS['CACHES']
    settings.CACHES.update({
        'tahoe_userprofile_metadata_cache': {
            'KEY_PREFIX': 'tahoe_userprofile_metadata',
            'LOCATION': settings.ENV_TOKENS.get('MEMCACHE_LOCATION', ['localhost:11211']),
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'MAX_ENTRIES': 100000  # estimated at <=30Mb. See BLACK-2636
        }
    })
