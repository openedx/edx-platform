from urllib import urlencode

import jwt
from opaque_keys.edx.keys import CourseKey
from w3lib.url import add_or_replace_parameter

from custom_settings.models import CustomSettings
from lms.envs.common import SOCIAL_SHARING_URLS, TWITTER_MESSAGE_FORMAT


def get_encoded_token(username, email, id):
    return jwt.encode({'id': id, 'username': username, 'email': email}, 'secret', algorithm='HS256')


def get_course_custom_settings(course_key):
    """ Return course custom settings object """
    if isinstance(course_key, str) or isinstance(course_key, unicode):
        course_key = CourseKey.from_string(course_key)

    return CustomSettings.objects.filter(id=course_key).first()


def get_social_sharing_urls(course_url, meta_tags, tweet_text=None):
    utm_params = meta_tags['utm_params'].copy()
    course_share_url = '{}?{}'.format(course_url, urlencode(utm_params))

    return {
        'facebook': _compile_social_sharing_url(
            SOCIAL_SHARING_URLS['facebook']['url'], course_share_url,
            SOCIAL_SHARING_URLS['facebook']['url_param'],
            SOCIAL_SHARING_URLS['facebook']['utm_source']
        ),

        'facebook_after_enroll': _compile_social_sharing_url(
            SOCIAL_SHARING_URLS['facebook']['url'],
            add_or_replace_parameter(course_share_url, 'share_after_enroll', 'true'),
            SOCIAL_SHARING_URLS['facebook']['url_param'],
            SOCIAL_SHARING_URLS['facebook']['utm_source']
        ),

        'linkedin': _compile_social_sharing_url(
            SOCIAL_SHARING_URLS['linkedin']['url'], course_share_url,
            SOCIAL_SHARING_URLS['linkedin']['url_param'],
            SOCIAL_SHARING_URLS['linkedin']['utm_source']
        ),

        'twitter': _compile_social_sharing_url(
            SOCIAL_SHARING_URLS['twitter']['url'], course_share_url,
            SOCIAL_SHARING_URLS['twitter']['url_param'],
            SOCIAL_SHARING_URLS['twitter']['utm_source'],
            text=TWITTER_MESSAGE_FORMAT.format(meta_tags['title'])
        ),

        'email': _compile_social_sharing_url(
            SOCIAL_SHARING_URLS['email']['url'], course_share_url,
            SOCIAL_SHARING_URLS['email']['url_param'],
            SOCIAL_SHARING_URLS['email']['utm_source']
        ),
    }


def _compile_social_sharing_url(share_url, course_url, url_param, utm_source, text=None):
    course_url_with_utm = add_or_replace_parameter(course_url, 'utm_source', utm_source)

    # Introduced for the email case where the addThis widget is being used
    if not share_url:
        return course_url_with_utm

    url = add_or_replace_parameter(share_url, url_param, course_url_with_utm)

    if text:
        url = add_or_replace_parameter(url, 'text', text)

    return url
