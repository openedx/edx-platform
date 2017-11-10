from urlparse import urlparse

from django.conf import settings
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
        'platform_name': site.configuration.get_value('platform_name', settings.PLATFORM_NAME),
        'contact_mailing_address': site.configuration.get_value(
            'contact_mailing_address',
            settings.CONTACT_MAILING_ADDRESS
        ),
        'social_media_urls': encode_urls_in_dict(
            site.configuration.get_value(
                'SOCIAL_MEDIA_FOOTER_URLS',
                getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})
            )
        ),
        'mobile_store_urls': encode_urls_in_dict(
            site.configuration.get_value(
                'MOBILE_STORE_URLS',
                getattr(settings, 'MOBILE_STORE_URLS', {})
            )

        ),
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
