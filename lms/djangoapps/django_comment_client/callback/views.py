import functools
import sys
import json
import logging
import pytz
import comment_client as cc
import django_comment_client.utils as utils

from dateutil.parser import parse
from time import strftime
from django.conf import settings
from django_comment_client.utils import JsonResponse, JsonError
from django.views.decorators.http import require_POST, require_GET
from django.core.urlresolvers import reverse
from django.views.decorators import csrf
from django.contrib.auth.models import User
from courseware.courses import get_course_by_id
from itertools import groupby

log = logging.getLogger("mitx.discussion")

def shared_key_auth_required(fn):
    @functools.wraps(fn)
    def wrapper(request, *args, **kwargs):
        if request.POST.get('api_key') != cc.settings.API_KEY:
            return JsonError("Authentication failed")
        else:
            return fn(request, *args, **kwargs)
    return wrapper

def process_replies(replies):
    def processor(wrapped_info):
        thread_id, grouped_replies = wrapped_info
        grouped_replies = list(grouped_replies)
        course_id = grouped_replies[0]['course_id']
        commentable_id = grouped_replies[0]['info']['commentable_id']
        return {
            'post_reply': True,
            'replies_count': len(grouped_replies),
            'thread_url': reverse('django_comment_client.forum.views.single_thread',
                                  args=[course_id, commentable_id, thread_id]),
            'happened_at': min(map(lambda x: x['happened_at'], grouped_replies)),
            'thread_title': grouped_replies[0]['info']['thread_title'],
        }
    replies = groupby(replies, lambda x: x['info']['thread_id'])
    return map(processor, [(k, list(v)) for k, v in replies])

def process_topics(topics):
    def process(notification):
        thread_id = notification['info']['thread_id']
        course_id = notification['course_id']
        commentable_id = notification['info']['commentable_id']
        return {
            'post_topic': True,
            'user_id': notification['info']['actor_id'],
            'username': notification['info']['actor_username'],
            'thread_url': reverse('django_comment_client.forum.views.single_thread',
                                args=[course_id, commentable_id, thread_id]),
            'happened_at': notification['happened_at'],
            'thread_title': notification['info']['thread_title'],
        }
    return map(process, topics)

def process_at_users(at_users):
    def process(notification):
        thread_id = notification['info']['thread_id']
        course_id = notification['course_id']
        commentable_id = notification['info']['commentable_id']
        content_type = notification['info']['content_type']
        data = {
            'at_user_in_' + content_type: True,
            'user_id': notification['info']['actor_id'],
            'username': notification['info']['actor_username'],
            'thread_url': reverse('django_comment_client.forum.views.single_thread',
                                  args=[course_id, commentable_id, thread_id]),
            'happened_at': notification['happened_at'],
            'thread_title': notification['info']['thread_title'],
        }
        if content_type == "comment":
            data['comment_url'] = data['thread_url'] + "#" + notification['info']['comment_id']
        return data
    return map(process, at_users)

@require_POST
@shared_key_auth_required
@csrf.csrf_exempt
def notifications_callback(request):
    course_id = request.POST['course_id']
    course = get_course_by_id(course_id)
    user_ids = json.loads(request.POST['json_user_ids'])
    raw_notifications = json.loads(request.POST['json_notifications'])

    if len(raw_notifications) == 0:
        return

    timezone = pytz.timezone(settings.TIME_ZONE)

    for notification in raw_notifications:
        notification['happened_at'] = parse(notification['happened_at']).astimezone(timezone)
    
    replies  = filter(lambda x: x.get('notification_type') == 'post_reply', raw_notifications)
    topics   = filter(lambda x: x.get('notification_type') == 'post_topic', raw_notifications)
    at_users = filter(lambda x: x.get('notification_type') == 'at_user', raw_notifications)

    notifications = process_replies(replies) + process_topics(topics) + process_at_users(at_users)
    notifications = sorted(notifications, key=lambda x: x['happened_at'])

    since_time = notifications[0]['happened_at'].strftime("%H:%M %p")

    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            context = {
                'course_name': course.org + ': ' + course.number + ' ' + course.title,
                'user': user,
                'notifications': notifications,
                'since_time': since_time,
            }
            # composes notifications email
            message = utils.render_mustache('discussion/emails/notifications_email.html.mustache', context)
            subject = utils.render_mustache('discussion/emails/notifications_email_subject.txt.mustache', context)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            res = user.email_user(subject, message, settings.DEFAULT_DISCUSSION_EMAIL)
        except:
            log.exception(sys.exc_info())
            return JsonError('Could not send notifications e-mail.')
    return JsonResponse({'status': 'success'})
