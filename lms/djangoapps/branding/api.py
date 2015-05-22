"""Edx branding API
"""
import logging
import os
from django.conf import settings
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.core.cache import cache
from staticfiles.storage import staticfiles_storage

from microsite_configuration import microsite
from edxmako.shortcuts import marketing_link

log = logging.getLogger("edx.footer")


def get_footer_json():
    """ Get the footer links json

    Returns:
        Dict of footer links
    """
    is_edx_domain = settings.FEATURES.get('IS_EDX_DOMAIN', False)
    key = "footer/json/{domain}".format(domain="edx" if is_edx_domain else "open_edx")
    footer_json = cache.get(key)
    if footer_json:
        return footer_json
    site_name = microsite.get_value('SITE_NAME', settings.SITE_NAME)

    context = dict()
    context["copy_right"] = copy_right(is_edx_domain)
    context["heading"] = heading(is_edx_domain)
    context["logo_img"] = get_footer_logo(site_name, is_edx_domain)
    context["social_links"] = social_links()
    context["about_links"] = about_edx_link()
    context["mobile_urls"] = get_mobile_urls()
    footer_json = {"footer": context}
    cache.set(key, footer_json)
    return footer_json


def copy_right(is_edx_domain):
    """ Returns the copy rights text
    """
    if is_edx_domain:
        data = _(
            "(c) 2015 edX Inc. EdX, Open edX, and the edX and Open edX logos "
            "are registered trademarks or trademarks of edX Inc."
        )
    else:
        data = _(
            "EdX, Open edX, and the edX and Open edX logos are registered trademarks or "
            "trademarks of {link_start}edX Inc.{link_end}"
        ).format(
            link_start=u"<a href='https://www.edx.org/'>",
            link_end=u"</a>"
        )

    return data


def heading(is_edx_domain):
    """ Returns the heading text copy
    """
    if is_edx_domain:
        data = _(
            "{EdX} offers interactive online classes and MOOCs from the world's best universities. "
            "Online courses from {MITx}, {HarvardX}, {BerkeleyX}, {UTx} and many other universities. "
            "Topics include biology, business, chemistry, computer science, economics, finance, "
            "electronics, engineering, food and nutrition, history, humanities, law, literature, "
            "math, medicine, music, philosophy, physics, science, statistics and more. {EdX} is a "
            "non-profit online initiative created by founding partners {Harvard} and {MIT}."
        ).format(
            EdX="EdX", Harvard="Harvard", MIT="MIT", HarvardX="HarvardX", MITx="MITx",
            BerkeleyX="BerkeleyX", UTx="UTx"
        )
    else:
        data = ""
    return data


def social_links():
    """ Returns the list of social link of footer
    """
    links = []
    for social_name in settings.SOCIAL_MEDIA_FOOTER_NAMES:
        links.append(
            {
                "provider": social_name,
                "title": unicode(settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name, {}).get("title", "")),
                "url": settings.SOCIAL_MEDIA_FOOTER_URLS.get(social_name, "#"),
                "social_icon": settings.SOCIAL_MEDIA_FOOTER_DISPLAY.get(social_name).get("icon", "")
            }
        )
    return links


def about_edx_link():
    """ Returns the list of marketing links of footer
    """

    return [
        {
            "title": _("About"),
            "url": marketing_link('ABOUT')
        },
        {
            "title": _("News"),
            "url": marketing_link('NEWS')
        },
        {
            "title": _("Contact"),
            "url": marketing_link('CONTACT')
        },
        {
            "title": _("FAQ"),
            "url": marketing_link('FAQ')
        },
        {
            "title": _("edX Blog"),
            "url": marketing_link('BLOG')
        },
        {
            "title": _("Donate to edX"),
            "url": marketing_link('DONATE')
        },
        {
            "title": _("Jobs at edX"),
            "url": marketing_link('JOBS')
        }
    ]


def get_footer_logo(site_name, is_edx_domain):
    """ Return the logo used for footer about link

    Args:
        site_name(str): The site url to get the absolute link
        is_edx_domain(bool): Flag to check is it in edx domain or open edx

    Returns:
        Absolute url to logo
    """
    if is_edx_domain:
        logo_file = 'images/edx-theme/edx-header-logo.png'
    else:
        logo_file = 'images/default-theme/logo.png'
    try:
        url = site_name + staticfiles_storage.url(logo_file)
    except:
        url = site_name + logo_file
    return url


def get_mobile_urls():
    """ Returns the mobile app urls

    """
    mobile_urls = []
    if settings.FEATURES.get('ENABLE_FOOTER_MOBILE_APP_LINKS'):
        mobile_urls = [
            {
                "title": "Apple",
                "url": settings.MOBILE_STORE_URLS.get('apple', '#'),
                "logo_image_url": 'images/app/app_store_badge_135x40.svg'
            },
            {
                "title": "Google",
                "url": settings.MOBILE_STORE_URLS.get('google', '#'),
                "logo_image_url": 'images/app/google_play_badge_45.png'
            }
        ]
    return mobile_urls


def get_footer_static(file_name):
    """ Returns the static js/css contents as a string

    Args:
        file_name(str): path to the static file name under static folder

    Raises:
        I/O Error if file not found
    Returns:
        Contents of static file

    """
    key = "footer/{file_name}".format(file_name=file_name)
    contents = cache.get(key)
    if contents:
        return contents
    file_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(file_dir, "static/{}".format(file_name))
    with open(file_path, "r") as _file:
        contents = _file.read()
    cache.set(key, contents)
    return contents


def get_footer_html():
    """ Return the html representation of footer

    """
    is_edx_domain = settings.FEATURES.get('IS_EDX_DOMAIN', False)
    key = "footer/html/{domain}".format(domain="edx" if is_edx_domain else "open_edx")
    response_string = cache.get(key)
    if response_string:
        return response_string
    if is_edx_domain:
        response_string = render_to_response("footer.html")
    else:
        response_string = render_to_response("footer-edx-new.html")
    cache.set(key, response_string)
    return response_string