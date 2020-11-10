"""
Defines asynchronous celery task for sending email notification (through edx-ace)
pertaining to new discussion forum comments.
"""


import logging

import six
from celery import task
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_ace.utils import date
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey
from six.moves.urllib.parse import urljoin

import openedx.core.djangoapps.django_comment_common.comment_client as cc
from lms.djangoapps.discussion.django_comment_client.utils import (
    get_accessible_discussion_xblocks_by_course_id,
    permalink
)
from openedx.core.djangoapps.ace_common.message import BaseMessageType
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.django_comment_common.models import DiscussionsIdMapping
from openedx.core.lib.celery.task_utils import emulate_http_request
from common.djangoapps.track import segment

log = logging.getLogger(__name__)


DEFAULT_LANGUAGE = 'en'
ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


@task(base=LoggedTask)
def update_discussions_map(context):
    """
    Updates the mapping between discussion_id to discussion block usage key
    for all discussion blocks in the given course.

    context is a dict that contains:
        course_id (string): identifier of the course
    """
    course_key = CourseKey.from_string(context['course_id'])
    discussion_blocks = get_accessible_discussion_xblocks_by_course_id(course_key, include_all=True)
    discussions_id_map = {
        discussion_block.discussion_id: six.text_type(discussion_block.location)
        for discussion_block in discussion_blocks
    }
    DiscussionsIdMapping.update_mapping(course_key, discussions_id_map)


class ResponseNotification(BaseMessageType):
    pass


@task(base=LoggedTask, routing_key=ROUTING_KEY)
def send_ace_message(context):
    context['course_id'] = CourseKey.from_string(context['course_id'])

    if _should_send_message(context):
        context['site'] = Site.objects.get(id=context['site_id'])
        thread_author = User.objects.get(id=context['thread_author_id'])
        with emulate_http_request(site=context['site'], user=thread_author):
            message_context = _build_message_context(context)
            message = ResponseNotification().personalize(
                Recipient(thread_author.username, thread_author.email),
                _get_course_language(context['course_id']),
                message_context
            )
            log.info(u'Sending forum comment email notification with context %s', message_context)
            ace.send(message)
            _track_notification_sent(message, context)


def _track_notification_sent(message, context):
    """
    Send analytics event for a sent email
    """
    properties = {
        'app_label': 'discussion',
        'name': 'responsenotification',  # This is 'Campaign' in GA
        'language': message.language,
        'uuid': six.text_type(message.uuid),
        'send_uuid': six.text_type(message.send_uuid),
        'thread_id': context['thread_id'],
        'course_id': six.text_type(context['course_id']),
        'thread_created_at': date.deserialize(context['thread_created_at']),
        'nonInteraction': 1,
    }
    tracking_context = {
        'host': context['site'].domain,
        'path': '/',  # make up a value, in order to allow the host to be passed along.
    }
    # The event used to specify the user_id as being the recipient of the email (i.e. the thread_author_id).
    # This has the effect of interrupting the actual chain of events for that author, if any, while the
    # email-sent event should really be associated with the sender, since that is what triggers the event.
    with tracker.get_tracker().context(properties['app_label'], tracking_context):
        segment.track(
            user_id=context['thread_author_id'],
            event_name='edx.bi.email.sent',
            properties=properties
        )


def _should_send_message(context):
    cc_thread_author = cc.User(id=context['thread_author_id'], course_id=context['course_id'])
    return (
        _is_user_subscribed_to_thread(cc_thread_author, context['thread_id']) and
        _is_not_subcomment(context['comment_id']) and
        _is_first_comment(context['comment_id'], context['thread_id'])
    )


def _is_not_subcomment(comment_id):
    comment = cc.Comment.find(id=comment_id).retrieve()
    return not getattr(comment, 'parent_id', None)


def _is_first_comment(comment_id, thread_id):
    thread = cc.Thread.find(id=thread_id).retrieve(with_responses=True)
    if getattr(thread, 'children', None):
        first_comment = thread.children[0]
        return first_comment.get('id') == comment_id
    else:
        return False


def _is_user_subscribed_to_thread(cc_user, thread_id):
    paginated_result = cc_user.subscribed_threads()
    thread_ids = {thread['id'] for thread in paginated_result.collection}

    while paginated_result.page < paginated_result.num_pages:
        next_page = paginated_result.page + 1
        paginated_result = cc_user.subscribed_threads(query_params={'page': next_page})
        thread_ids.update(thread['id'] for thread in paginated_result.collection)

    return thread_id in thread_ids


def _get_course_language(course_id):
    course_overview = CourseOverview.objects.get(id=course_id)
    language = course_overview.language or DEFAULT_LANGUAGE
    return language


def _build_message_context(context):
    message_context = get_base_template_context(context['site'])
    message_context.update(context)
    thread_author = User.objects.get(id=context['thread_author_id'])
    comment_author = User.objects.get(id=context['comment_author_id'])
    message_context.update({
        'thread_username': thread_author.username,
        'comment_username': comment_author.username,
        'post_link': _get_thread_url(context),
        'comment_created_at': date.deserialize(context['comment_created_at']),
        'thread_created_at': date.deserialize(context['thread_created_at'])
    })
    return message_context


def _get_thread_url(context):
    thread_content = {
        'type': 'thread',
        'course_id': context['course_id'],
        'commentable_id': context['thread_commentable_id'],
        'id': context['thread_id'],
    }
    return urljoin(context['site'].domain, permalink(thread_content))
