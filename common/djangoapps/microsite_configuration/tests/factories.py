"""
Factories module to hold microsite factories
"""
import factory
from factory.django import DjangoModelFactory

from django.contrib.sites.models import Site

from microsite_configuration.models import (
    Microsite,
    MicrositeOrganizationMapping,
    MicrositeTemplate,
)


class SiteFactory(DjangoModelFactory):
    """
    Factory for django.contrib.sites.models.Site
    """
    class Meta(object):
        model = Site

    name = "test microsite"
    domain = "testmicrosite.testserver"


class MicrositeFactory(DjangoModelFactory):
    """
    Factory for Microsite
    """
    class Meta(object):
        model = Microsite

    key = "test_microsite"
    site = factory.SubFactory(SiteFactory)
    values = {
        "domain_prefix": "testmicrosite",
        "university": "test_microsite",
        "platform_name": "Test Microsite DB",
        "logo_image_url": "test_microsite/images/header-logo.png",
        "email_from_address": "test_microsite_db@edx.org",
        "payment_support_email": "test_microsit_dbe@edx.org",
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
        "nested_dict": {
            "key 1": "value 1",
            "key 2": "value 2",
        }
    }


class MicrositeOrganizationMappingFactory(DjangoModelFactory):
    """
    Factory for MicrositeOrganizationMapping
    """
    class Meta(object):
        model = MicrositeOrganizationMapping


class MicrositeTemplateFactory(DjangoModelFactory):
    """
    Factory for MicrositeTemplate
    """
    class Meta(object):
        model = MicrositeTemplate
