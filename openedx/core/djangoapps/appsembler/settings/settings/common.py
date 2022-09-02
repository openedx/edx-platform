"""
Common Appsembler settings for all environments in both LMS and CMS.
"""


def plugin_settings(settings):
    """
    Appsembler overrides for all of the environments (devstack, prod and test) in both of CMS and LMS.

    This is a useful place for placing Appsembler-wide settings, for production
    and devstack settings checkout the other `production_common.py` and `common_devstack.py` sibling files.
    """
    settings.APPSEMBLER_FEATURES = {}

    settings.INSTALLED_APPS += [
        'compat',
        'hijack',
        'hijack_admin',

        'openedx.core.djangoapps.appsembler.i18n',
        'openedx.core.djangoapps.appsembler.sites',
        'openedx.core.djangoapps.appsembler.html_certificates',
        'openedx.core.djangoapps.appsembler.api',
        'openedx.core.djangoapps.appsembler.auth.apps.AppsemblerAuthConfig',
    ]

    # insert at beginning because it needs to be earlier in the list than various
    # redirect middleware which will cause later `process_request()` methods to be skipped
    settings.MIDDLEWARE.insert(
        0, 'beeline.middleware.django.HoneyMiddleware'
    )

    # Disable PDF certificates on Tahoe by default because we only support HTML certificate
    # This is a custom Tahoe feature flag.
    # TODO: Add tests for the feature
    settings.FEATURES['ENABLE_TAHOE_PDF_CERTS'] = False

    settings.DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors'] += (
        'openedx.core.djangoapps.appsembler.intercom_integration.context_processors.intercom',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.google_analytics',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.hubspot',
        'openedx.core.djangoapps.appsembler.analytics.context_processors.mixpanel',
    )

    # Tahoe: fix: "Invalid type for parameter ContentType" error on js upload
    #
    #    This fix is useless in the Maple release.
    #    The upstream Open edX fix is https://github.com/edx/edx-platform/pull/25957
    #    For more details see: https://github.com/jazzband/django-pipeline/pull/715
    #
    settings.PIPELINE['MIMETYPES'] = (
        (str('text/coffeescript'), str('.coffee')),
        (str('text/less'), str('.less')),
        (str('text/javascript'), str('.js')),
        (str('text/x-sass'), str('.sass')),
        (str('text/x-scss'), str('.scss')),
    )

    settings.SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

    settings.CLONE_COURSE_FOR_NEW_SIGNUPS = False
    settings.HIJACK_ALLOW_GET_REQUESTS = True
    settings.HIJACK_LOGOUT_REDIRECT_URL = '/admin/auth/user'

    # This flag should be removed when we fully migrate all of Tahoe fork to Juniper
    # until then, instead of commenting out code, this flag should be used so we can easily find
    # and fix test issues

    settings.TAHOE_ENABLE_CUSTOM_ERROR_VIEW = True  # Use the Django default error page during testing
    settings.CUSTOMER_THEMES_BACKEND_OPTIONS = {
        'location': 'customer_themes',
    }

    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_TIMEOUT = None  # The length of time we cache Redirect model data
    settings.CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX = 'custom_domains_redirects'

    settings.COPY_SEGMENT_EVENT_PROPERTIES_TO_TOP_LEVEL = False

    settings.EVENT_TRACKING_PROCESSORS += [
        # This processor does nothing outside of LMS but it's easier to keep this in common settings
        # but we could look at just putting this in the `_lms` modules, too.
        {
            'ENGINE': 'openedx.core.djangoapps.appsembler.eventtracking.tahoeusermetadata.TahoeUserMetadataProcessor'
        }
    ]

    # Appsembler allows generating honor certs
    settings.FEATURES['TAHOE_AUTO_GENERATE_HONOR_CERTS'] = True

    # Off by default. See the `site_configuration.tahoe_organization_helpers.py` module.
    settings.FEATURES['TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT'] = False
