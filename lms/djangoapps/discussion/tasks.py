import logging
from urllib import urlencode
from urlparse import urlparse

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from celery_utils.logged_task import LoggedTask
from edx_ace import ace
from edx_ace.channel import ChannelType
from edx_ace.message import Message, MessageType
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from edxmako.shortcuts import marketing_link
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration.helpers import get_value
from lms.lib.comment_client.user import User as CommentClientUser
from lms.lib.comment_client.utils import merge_dict

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


DEFAULT_LANGUAGE = 'en'
ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


class ResponseNotification(MessageType):
    def __init__(self, *args, **kwargs):
        super(ResponseNotification, self).__init__(*args, **kwargs)
        self.name = 'response_notification'


@task(base=LoggedTask, routing_key=ROUTING_KEY)
def send_ace_message(thread_id, thread_author_id, comment_author_id, course_id):
    thread_author = User.objects.get(id=thread_author_id)
    cc_thread_author = CommentClientUser.from_django_user(thread_author)

    if cc_thread_author.is_user_subscribed_to_thread(course_id, thread_id):
        comment_author = User.objects.get(id=comment_author_id)

        message = ResponseNotification().personalize(
            Recipient(thread_author.username, thread_author.email),
            _get_course_language(course_id),
            _build_email_context(comment_author, thread_id)
        )
        # ace.send(message)


def _build_email_context(comment_author, thread_id):
    # these will be passed in via context
    course_key = None
    thread_author = None
    return merge_dict(
        _get_base_template_context(Site.objects.get_current()),
        {
            'comment_author': comment_author,
            'thread_id': thread_id,
            'ga_pixel_url': _generate_ga_pixel_url(course_key=course_key, user_id=thread_author.id),
        }
    )


def _get_course_language(course_id):
    try:
        course_key = CourseKey.from_string(kwargs['course_id'])
        course_overview = CourseOverview.objects.get(id=course_key)
        language = course_overview.language or DEFAULT_LANGUAGE
    except:
        language = DEFAULT_LANGUAGE
    return language


def _get_base_template_context(site):
    """Dict with entries needed for all templates that use the base template"""
    return {
        # Platform information
        'homepage_url': _encode_url(marketing_link('ROOT')),
        'dashboard_url': _absolute_url(site, reverse('dashboard')),
        'ga_pixel_url': _generate_ga_pixel_url(),
        'template_revision': settings.EDX_PLATFORM_REVISION,
        'platform_name': settings.PLATFORM_NAME,
        'contact_mailing_address': settings.CONTACT_MAILING_ADDRESS,
        'social_media_urls': _encode_urls_in_dict(getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})),
        'mobile_store_urls': _encode_urls_in_dict(getattr(settings, 'MOBILE_STORE_URLS', {})),
    }


def _encode_url(url):
    # Sailthru has a bug where URLs that contain "+" characters in their path components are misinterpreted
    # when GA instrumentation is enabled. We need to percent-encode the path segments of all URLs that are
    # injected into our templates to work around this issue.
    parsed_url = urlparse(url)
    modified_url = parsed_url._replace(path=urlquote(parsed_url.path))
    return modified_url.geturl()


def _absolute_url(site, relative_path):
    root = site.domain.rstrip('/')
    relative_path = relative_path.lstrip('/')
    return _encode_url(u'https://{root}/{path}'.format(root=root, path=relative_path))


def _encode_urls_in_dict(mapping):
    urls = {}
    for key, value in mapping.iteritems():
        urls[key] = _encode_url(value)
    return urls


def _generate_ga_pixel_url(course_key, user_id):
    # used for analytics
    query_params = {
        'v': '1',
        't': 'event',
        'ec': 'email',
        'ea': 'open',
        'tid': get_value("GOOGLE_ANALYTICS_TRACKING_ID", settings.GOOGLE_ANALYTICS_TRACKING_ID),
        'uid': user_id,
        'utm_source': 'discussion_notification_email',
        'utm_medium': 'email',
        'cm': 'email',
        'cn': 'discussions_notifications_emails',
        'dp': '/email/ace/discussions/responsenotification/{0}/'.format(course_key),
        'dt': 'To Be Filled In',
    }

    url = u"{url}?{params}".format(
        url="https://www.google-analytics.com/collect",
        params=urlencode(query_params)
    )

    return _encode_url(url)