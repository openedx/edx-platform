"""
Factories module to hold microsite factories
"""

from factory.django import DjangoModelFactory

from microsite_configuration.models import (
    Microsite,
    MicrositeOrgMapping,
)


class MicrositeFactory(DjangoModelFactory):

    class Meta(object):
        model = Microsite

    key = "test_microsite"
    subdomain = "testmicrosite.testserver"
    values = {
        "domain_prefix": "testmicrosite",
        "university": "test_microsite",
        "platform_name": "Test Microsite",
        "logo_image_url": "test_microsite/images/header-logo.png",
        "email_from_address": "test_microsite@edx.org",
        "payment_support_email": "test_microsite@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "test_microsite.localhost",
        "course_org_filter": "TestMicrositeX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_microsite/css/test_microsite.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "This is a Test Microsite Overlay Text.",
        "course_index_overlay_logo_file": "test_microsite/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Test Microsite Overlay HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
        "COURSE_CATALOG_VISIBILITY_PERMISSION": "see_in_catalog",
        "COURSE_ABOUT_VISIBILITY_PERMISSION": "see_about_page",
        "ENABLE_SHOPPING_CART": True,
        "ENABLE_PAID_COURSE_REGISTRATION": True,
        "SESSION_COOKIE_DOMAIN": "test_microsite.localhost",
    }


class MicrositeOrgMappingFactory(DjangoModelFactory):

    class Meta(object):
        model = MicrositeOrgMapping
