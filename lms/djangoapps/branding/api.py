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

from django.conf import settings
from django.utils.translation import ugettext as _
from staticfiles.storage import staticfiles_storage

from microsite_configuration import microsite
from edxmako.shortcuts import marketing_link

log = logging.getLogger("edx.footer")


def get_footer(is_secure=True):
    """Retrieve information used to render the footer.

    This will handle both the OpenEdX and EdX.org versions
    of the footer.  All user-facing text is internationalized.

    Currently, this does NOT support theming.

    Keyword Arguments:
        is_secure (bool): If True, use https:// in URLs.

    Returns: dict

    Example:
    >>> get_footer()
    {
        "copyright": "(c) 2015 EdX Inc",
        "logo_image": "http://www.example.com/logo.png",
        "social_links": [
            {
                "name": "facebook",
                "title": "Facebook",
                "url": "http://www.facebook.com/example",
                "icon-class": "fa-facebook-square"
            },
            ...
        ],
        "navigation_links": [
            {
                "name": "about",
                "title": "About",
                "url": "http://www.example.com/about.html"
            },
            ...
        ],
        "mobile_links": [
            {
                "name": "apple",
                "title": "Apple",
                "url": "http://store.apple.com/example_app"
                "image": "http://example.com/static/apple_logo.png"
            },
            ...
        ],
        "openedx_link": {
            "url": "http://open.edx.org",
            "title": "Powered by Open edX",
            "image": "http://example.com/openedx.png"
        }
    }

    """
    is_edx_domain = settings.FEATURES.get('IS_EDX_DOMAIN', False)
    site_name = microsite.get_value('SITE_NAME', settings.SITE_NAME)

    return {
        "copyright": _footer_copyright(is_edx_domain),
        "logo_image": _footer_logo_img(is_secure, site_name, is_edx_domain),
        "social_links": _footer_social_links(),
        "navigation_links": _footer_navigation_links(),
        "mobile_links": _footer_mobile_links(is_secure, site_name),
        "openedx_link": _footer_openedx_link(is_secure, site_name),
    }


def _footer_copyright(is_edx_domain):
    """Return the copyright to display in the footer.

    Arguments:
        is_edx_domain (bool): If true, this is an EdX-controlled domain.

    Returns: unicode

    """
    org_name = (
        "edX Inc" if is_edx_domain
        else microsite.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
    )

    # Translators: 'EdX', 'edX', and 'Open edX' are trademarks of 'edX Inc.'.
    # Please do not translate any of these trademarks and company names.
    return _(
        u"\u00A9 {org_name}.  All rights reserved except where noted.  "
        u"EdX, Open edX and the edX and OpenEdX logos are registered trademarks "
        u"or trademarks of edX Inc."
    ).format(org_name=org_name)


def _footer_openedx_link(is_secure, site_name):
    """Return the image link for "powered by OpenEdX".

    Args:
        is_secure (bool): Whether the request is using TLS.
        site_name (str): The site url to get the absolute link

    Returns: dict

    """
    return {
        "url": "http://open.edx.org",
        "title": _("Powered by Open edX"),
        "image": _absolute_url(is_secure, site_name, "images/openedx-logo-tag.png")
    }


def _footer_social_links():
    """Return the social media links to display in the footer.

    Returns: list

    """
    links = []
    for social_name in settings.SOCIAL_MEDIA_FOOTER_NAMES:
        links.append(
            {
                "name": social_name,
                "title": unicode(settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name, {}).get("title", "")),
                "url": settings.SOCIAL_MEDIA_FOOTER_URLS.get(social_name, "#"),
                "icon-class": settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name, {}).get("icon", ""),
            }
        )
    return links


def _footer_navigation_links():
    """Return the navigation links to display in the footer. """
    # TODO: make the order configurable in Django settings
    # TODO: make the title a Django setting
    return [
        {
            "name": "about",
            "title": _("About"),
            "url": marketing_link("ABOUT")
        },
        {
            "name": "news",
            "title": _("News"),
            "url": marketing_link("NEWS")
        },
        {
            "name": "contact",
            "title": _("Contact"),
            "url": marketing_link("CONTACT")
        },
        {
            "name": "faq",
            "title": _("FAQ"),
            "url": marketing_link("FAQ")
        },
        {
            "name": "blog",
            "title": _("edX Blog"),
            "url": marketing_link("BLOG")
        },
        {
            "name": "donate",
            "title": _("Donate to edX"),
            "url": marketing_link("DONATE")
        },
        {
            "name": "jobs",
            "title": _("Jobs at edX"),
            "url": marketing_link("JOBS")
        },
        {
            "name": "terms_of_service",
            "title": _("Terms of Service"),
            "url": marketing_link("TOS")
        },
        {
            "name": "privacy_policy",
            "title": _("Privacy Policy"),
            "url": marketing_link("PRIVACY")
        }
    ]


def _footer_mobile_links(is_secure, site_name):
    """Return the mobile app store links.

    Args:
        is_secure (bool): Whether the request is using TLS.
        site_name (str): The site url to get the absolute link

    Returns: list

    """
    mobile_links = []
    if settings.FEATURES.get('ENABLE_FOOTER_MOBILE_APP_LINKS'):
        mobile_links = [
            {
                "name": "apple",
                "title": "Apple",
                "url": settings.MOBILE_STORE_URLS.get('apple', '#'),
                "image": _absolute_url(is_secure, site_name, 'images/app/app_store_badge_135x40.svg')
            },
            {
                "name": "google",
                "title": "Google",
                "url": settings.MOBILE_STORE_URLS.get('google', '#'),
                "image": _absolute_url(is_secure, site_name, 'images/app/google_play_badge_45.png')
            }
        ]
    return mobile_links


def _footer_logo_img(is_secure, site_name, is_edx_domain):
    """Return the logo used for footer about link

    Args:
        is_secure (bool): Whether the request is using TLS.
        site_name(str): The site url to get the absolute link
        is_edx_domain (bool): If true, this is an EdX-controlled domain.

    Returns:
        Absolute url to logo
    """
    logo_name = (
        u"images/edx-theme/edx-header-logo.png"
        if is_edx_domain
        else u"images/default-theme/logo.png"
    )

    return _absolute_url(is_secure, site_name, logo_name)


def _absolute_url(is_secure, site_name, name):
    """Construct an absolute URL back to the site.

    Arguments:
        is_secure (bool): If true, use HTTPS as the protocol.
        site_name (unicode): The site name of this server.
        path (unicode): The URL path.

    Returns:
        unicode

    """
    url_path = staticfiles_storage.url(name)
    protocol = "https://" if is_secure else "http://"
    return u"{protocol}{site_name}{url_path}".format(
        protocol=protocol,
        site_name=site_name,
        url_path=url_path
    )
