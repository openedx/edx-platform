"""
Defines the sharing sites for different social media platforms
"""
from collections import namedtuple
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlencode

TWITTER_SHARE_MESSAGE = _("Here's a fun clip from a class I'm taking on @edXonline.\n\n")

SharingSiteConfig = namedtuple(
    'SharingSiteConfig',
    [
        'name',
        'fa_icon_name',
        'url_param_name',
        'base_share_url',
        'additional_site_params'
    ],
    defaults=[{}]
)

TWITTER = SharingSiteConfig(
    name='twitter',
    fa_icon_name='fa-twitter-square',
    url_param_name='url',
    base_share_url='https://twitter.com/intent/tweet',
    additional_site_params={'text': TWITTER_SHARE_MESSAGE}
)

FACEBOOK = SharingSiteConfig(
    name='facebook',
    fa_icon_name='fa-facebook-square',
    url_param_name='u',
    base_share_url='https://www.facebook.com/sharer/sharer.php'
)

LINKEDIN = SharingSiteConfig(
    name='linkedin',
    fa_icon_name='fa-linkedin-square',
    url_param_name='url',
    base_share_url='https://www.linkedin.com/sharing/share-offsite/'
)

ALL_SHARING_SITES = [
    TWITTER,
    FACEBOOK,
    LINKEDIN,
]


def sharing_sites_info_for_video(video_public_url):
    """
    Returns a list of dicts, each containing the name, fa_icon_name, and sharing_url
    """
    result = []
    for sharing_site_config in ALL_SHARING_SITES:
        sharing_site_info = {
            'name': sharing_site_config.name,
            'fa_icon_name': sharing_site_config.fa_icon_name,
            'sharing_url': sharing_url(
                video_public_url,
                sharing_site_config
            )
        }
        result.append(sharing_site_info)
    return result


def sharing_url(video_public_url, sharing_site_config):
    """
    Returns the sharing url with the appropriate parameters
    """
    share_params = {
        'utm_source': sharing_site_config.name,
        'utm_medium': 'social',
        'utm_campaign': 'social-share-exp',
        sharing_site_config.url_param_name: video_public_url
    }
    share_params.update(sharing_site_config.additional_site_params)
    return sharing_site_config.base_share_url + '?' + urlencode(share_params)
