"""EdX Branding API

Provides a way to retrieve "branded" parts of the site,
such as the site footer.

This information exposed to:
1) Templates in the LMS.
2) Consumers of the branding API.

This ensures that branded UI elements such as the footer
are consistent across the LMS and other sites (such as
the marketing site and blog).

"""
import logging
import urlparse

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.translation import ugettext as _

from branding.models import BrandingApiConfig
from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger("edx.footer")
EMPTY_URL = '#'


def is_enabled():
    """Check whether the branding API is enabled. """
    return BrandingApiConfig.current().enabled


def get_auth_footer():
    """ Override default get_footer method & add link for after authentication pages"""
    return {
        "copyright": _auth_footer_copyright(),
        "social_links": _auth_footer_social_links(),
        "navigation_links": _auth_footer_navigation_links(),
        "courses_communities_links": _auth_footer_courses_communities_links(),
        "legal_links": _auth_footer_legal_links(),
    }


def get_non_auth_footer():
    """ Override default get_footer method """

    return {
        "copyright": _footer_copyright(),
        "social_links": _footer_social_links(),
        "navigation_links": _footer_navigation_links(),
        "legal_links": my_footer_legal_links(),
    }


def _auth_footer_copyright():
    """Return the copyright to display in the footer.

    Returns: unicode

    """
    return _(
        # Translators: 'EdX', 'edX', and 'Open edX' are trademarks of 'edX Inc.'.
        # Please do not translate any of these trademarks and company names.
        u"\u00A9 {org_name}.  All rights reserved except where noted.  "
        u"EdX, Open edX and the edX and Open EdX logos are registered trademarks "
        u"or trademarks of edX Inc."
    ).format(org_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME))


def _footer_copyright():
    """Return the copyright to display in the footer.

    Returns: unicode

    """
    return _(
        # Translators: 'EdX', 'edX', and 'Open edX' are trademarks of 'edX Inc.'.
        # Please do not translate any of these trademarks and company names.
        u"\u00A9 {org_name}.  All rights reserved except where noted.  "
        u"EdX, Open edX and the edX and Open EdX logos are registered trademarks "
        u"or trademarks of edX Inc."
    ).format(org_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME))


def _auth_footer_social_links():
    """Return the social media links to display in the footer.

    Returns: list

    """
    platform_name = configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
    links = []

    for social_name in settings.SOCIAL_MEDIA_FOOTER_NAMES:
        display = settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name, {})
        links.append(
            {
                "name": social_name,
                "title": unicode(display.get("title", "")),
                "url": settings.SOCIAL_MEDIA_FOOTER_URLS.get(social_name, "#"),
                "icon-class": display.get("icon", ""),
                "action": unicode(display.get("action", "")).format(platform_name=platform_name),
            }
        )
    return links


def _footer_social_links():
    """Return the social media links to display in the footer.

    Returns: list

    """
    platform_name = configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME)
    links = []

    for social_name in settings.SOCIAL_MEDIA_FOOTER_NAMES:
        display = settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name, {})
        links.append(
            {
                "name": social_name,
                "title": unicode(display.get("title", "")),
                "url": settings.SOCIAL_MEDIA_FOOTER_URLS.get(social_name, "#"),
                "icon-class": display.get("icon", ""),
                "action": unicode(display.get("action", "")).format(platform_name=platform_name),
            }
        )
    return links


def _auth_footer_navigation_links():
    """Return the navigation links to display in the footer. """
    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
            "target": link_target,
        }
        for link_name, link_url, link_title, link_target in [
            ("about", "https://philanthropyu.org", "About Philanthropy University", "_blank"),
            ("perks", "https://philanthropyu.org/perks", "Perks", "_blank"),
        ]
    ]


def _auth_footer_courses_communities_links():
    """Return the navigation links to display in the footer. """
    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
            "target": link_target,
            "class": link_class
        }
        for link_name, link_url, link_title, link_target, link_class in [
            ("explore_course", "/courses", _("Explore our Courses"), "_self", "track-gtm-event"),
            ("mentors", "https://philanthropyu.org/mentors", "Mentors", "_blank", ""),
            ("google-ad-grants", "https://philanthropyu.org/ad-grants", "Google Ad Grants", "_blank", ""),
        ]
    ]


def _footer_navigation_links():
    """Return the navigation links to display in the footer. """
    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
            "target": link_target,
            "class": link_class
        }
        for link_name, link_url, link_title, link_target, link_class in [
            ("about", "https://philanthropyu.org", "About Philanthropy University", "blank", ""),
            ("perks", "https://philanthropyu.org/perks", "Perks", "_blank", ""),
        ]
    ]


def _auth_footer_legal_links():
    """Return the legal footer links (e.g. terms of service). """
    links = [
        ("terms_of_service_and_honor_code", "https://philanthropyu.org/terms-of-use/", _("Terms of Use"), "_blank"),
        ("privacy_policy", "https://philanthropyu.org/privacy-policy/", _("Privacy Policy"), "_blank"),
        ("faq", "https://support.philanthropyu.org", _("FAQ"), "_blank")
    ]

    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
            "target": link_target,
        }
        for link_name, link_url, link_title, link_target in links
        if link_url and link_url != "#"
    ]


def my_footer_legal_links():
    """Return the legal footer links (e.g. terms of service). """

    links = [
        ("terms_of_service_and_honor_code", "https://philanthropyu.org/terms-of-use/", _("Terms of Use"), "_blank"),
        ("privacy_policy", "https://philanthropyu.org/privacy-policy/", _("Privacy Policy"), "_blank"),
        ("faq", "https://support.philanthropyu.org", _("FAQ"), "_blank")
    ]

    return [
        {
            "name": link_name,
            "title": link_title,
            "url": link_url,
            "target": link_target,
        }
        for link_name, link_url, link_title, link_target in links
        if link_url and link_url != "#"
    ]


def _absolute_url(is_secure, url_path):
    """Construct an absolute URL back to the site.

    Arguments:
        is_secure (bool): If true, use HTTPS as the protocol.
        url_path (unicode): The path of the URL.

    Returns:
        unicode

    """
    site_name = configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME)
    parts = ("https" if is_secure else "http", site_name, url_path, '', '', '')
    return urlparse.urlunparse(parts)


def _absolute_url_staticfile(is_secure, name):
    """Construct an absolute URL to a static resource on the site.

    Arguments:
        is_secure (bool): If true, use HTTPS as the protocol.
        name (unicode): The name of the static resource to retrieve.

    Returns:
        unicode

    """
    url_path = staticfiles_storage.url(name)

    # In production, the static files URL will be an absolute
    # URL pointing to a CDN.  If this happens, we can just
    # return the URL.
    if urlparse.urlparse(url_path).netloc:
        return url_path

    # For local development, the returned URL will be relative,
    # so we need to make it absolute.
    return _absolute_url(is_secure, url_path)


def get_configuration_url(name):
    """
    Look up and return the value for given url name in configuration.
    URLs are saved in "urls" dictionary inside configuration.

    Return 'EMPTY_URL' if given url name is not defined in configuration urls.
    """
    urls = configuration_helpers.get_value("urls", default={})
    return urls.get(name) or EMPTY_URL


def get_url(name):
    """
    Lookup and return page url, lookup is performed in the following order

    1. get url, If configuration URL override exists, return it
    2. Otherwise return the marketing URL.

    :return: string containing page url.
    """
    # If a configuration URL override exists, return it.  Otherwise return the marketing URL.
    configuration_url = get_configuration_url(name)
    if configuration_url != EMPTY_URL:
        return configuration_url

    # get marketing link, if marketing is disabled then platform url will be used instead.
    url = marketing_link(name)

    return url or EMPTY_URL


def get_base_url(is_secure):
    """
    Return Base URL for site.
    Arguments:
        is_secure (bool): If true, use HTTPS as the protocol.
    """
    return _absolute_url(is_secure=is_secure, url_path="")


def get_logo_url(is_secure=True):
    """
    Return the url for the branded logo image to be used
    Arguments:
        is_secure (bool): If true, use HTTPS as the protocol.
    """

    # if the configuration has an overide value for the logo_image_url
    # let's use that
    image_url = configuration_helpers.get_value('logo_image_url')
    if image_url:
        return _absolute_url_staticfile(
            is_secure=is_secure,
            name=image_url,
        )

    # otherwise, use the legacy means to configure this
    university = configuration_helpers.get_value('university')

    if university:
        return staticfiles_storage.url('images/{uni}-on-edx-logo.png'.format(uni=university))
    else:
        return staticfiles_storage.url('images/logo.png')


def get_tos_and_honor_code_url():
    """
    Lookup and return terms of services page url
    """
    return get_url("TOS_AND_HONOR")


def get_privacy_url():
    """
    Lookup and return privacy policies page url
    """
    return get_url("PRIVACY")


def get_about_url():
    """
    Lookup and return About page url
    """
    return get_url("ABOUT")
