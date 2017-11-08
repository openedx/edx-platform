from urlparse import urlparse

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from edxmako.shortcuts import marketing_link


def get_base_template_context(site):
    """Dict with entries needed for all templates that use the base template"""
    return {
        # Platform information
        'homepage_url': encode_url(marketing_link('ROOT')),
        'dashboard_url': absolute_url(site, reverse('dashboard')),
        'template_revision': settings.EDX_PLATFORM_REVISION,
        'platform_name': settings.PLATFORM_NAME,
        'contact_mailing_address': settings.CONTACT_MAILING_ADDRESS,
        'social_media_urls': encode_urls_in_dict(getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})),
        'social_media_icons': encode_urls_in_dict(get_social_media_footer_icons(site)),
        'mobile_store_urls': encode_urls_in_dict(getattr(settings, 'MOBILE_STORE_URLS', {})),
        'mobile_store_icons': encode_urls_in_dict(get_mobile_store_footer_icons(site)),
        'edx_logo': encode_url(absolute_url(site, static('images/bulk_email/edx-logo-77x36.png'))),
    }


def get_social_media_footer_icons(site):
    return {
        'linkedin': absolute_url(site, static('images/bulk_email/LinkedInIcon_gray.png')),
        'twitter': absolute_url(site, static('images/bulk_email/TwitterIcon_gray.png')),
        'facebook': absolute_url(site, static('images/bulk_email/FacebookIcon_gray.png')),
        'google_plus': absolute_url(site, static('images/bulk_email/GooglePlusIcon_gray.png')),
        'youtube': absolute_url(site, static('images/bulk_email/YoutubeIcon_gray.png')),
    }


def get_mobile_store_footer_icons(site):
    return {
        'google': absolute_url(site, static('images/bulk_email/google_play_badge_45.png')),
        'apple': absolute_url(site, static('images/bulk_email/app_store_badge_135x40.svg')),
    }


def encode_url(url):
    # Sailthru has a bug where URLs that contain "+" characters in their path components are misinterpreted
    # when GA instrumentation is enabled. We need to percent-encode the path segments of all URLs that are
    # injected into our templates to work around this issue.
    parsed_url = urlparse(url)
    modified_url = parsed_url._replace(path=urlquote(parsed_url.path))
    return modified_url.geturl()


def absolute_url(site, relative_path):
    """
    Add site.domain to the beginning of the given relative path.

    If the given URL is already absolute (has a netloc part), then it is just returned.
    """
    if bool(urlparse(relative_path).netloc):
        # Given URL is already absolute
        return relative_path
    root = site.domain.rstrip('/')
    relative_path = relative_path.lstrip('/')
    return encode_url(u'https://{root}/{path}'.format(root=root, path=relative_path))


def encode_urls_in_dict(mapping):
    urls = {}
    for key, value in mapping.iteritems():
        urls[key] = encode_url(value)
    return urls
