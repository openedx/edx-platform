import jwt
from custom_settings.models import CustomSettings
from opaque_keys.edx.keys import CourseKey
from urllib import urlencode
from w3lib.url import add_or_replace_parameter


def get_encoded_token(username, email, id):
    return jwt.encode({'id': id, 'username': username, 'email': email }, 'secret', algorithm='HS256')


def get_course_custom_settings(course_key):
    """ Return course custom settings object """
    if isinstance(course_key, str) or isinstance(course_key, unicode):
        course_key = CourseKey.from_string(course_key)

    return CustomSettings.objects.filter(id=course_key).first()


def get_social_sharing_urls(course_url, meta_tags):
    social_sharing_urls = {}
    utm_params = meta_tags['utm_params'].copy()
    share_url = '{}?{}'.format(course_url, urlencode(utm_params))

    # Facebook
    facebook_share_url = 'https://www.facebook.com/sharer/sharer.php'
    share_url = add_or_replace_parameter(share_url, 'utm_source', 'Facebook')
    social_sharing_urls['facebook'] = add_or_replace_parameter(facebook_share_url, 'u', share_url)

    # LinkedIn url
    linkedin_share_url = 'http://www.linkedin.com/shareArticle?mini=true'
    share_url = add_or_replace_parameter(share_url, 'utm_source', 'LinkedIn')
    social_sharing_urls['linkedin'] = add_or_replace_parameter(linkedin_share_url, 'url', share_url)

    return social_sharing_urls
