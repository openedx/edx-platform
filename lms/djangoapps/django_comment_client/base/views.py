import functools
import logging
import json
import random
import time
import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import exceptions
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators import csrf
from django.views.decorators.http import require_GET, require_POST
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.access import has_access
from util.file import store_uploaded_file
from courseware.courses import get_course_with_access, get_course_overview_with_access, get_course_by_id
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    get_notification_type
)
from edx_notifications.data import NotificationMessage
from courseware.courses import get_course_with_access, get_course_by_id
from openedx.core.djangoapps.course_groups.tasks import publish_course_group_notification_task
import django_comment_client.settings as cc_settings
from django_comment_common.signals import (
    thread_created,
    thread_edited,
    thread_voted,
    thread_deleted,
    comment_created,
    comment_edited,
    comment_voted,
    comment_deleted,
    comment_endorsed,
)
from django_comment_common.utils import ThreadContext
from django_comment_client.utils import (
    add_courseware_context,
    get_annotated_content_info,
    get_ability,
    is_comment_too_deep,
    JsonError,
    JsonResponse,
    prepare_content,
    get_group_id_for_comments_service,
    discussion_category_id_access,
    get_cached_discussion_id_map,
    add_thread_group_name,
)
from django_comment_client.permissions import check_permissions_by_view, has_permission, get_team
from eventtracking import tracker
from util.html import strip_tags
import lms.lib.comment_client as cc

from social_engagement.engagement import update_user_engagement_score

log = logging.getLogger(__name__)

TRACKING_MAX_FORUM_BODY = 2000
_EVENT_NAME_TEMPLATE = 'edx.forum.{obj_type}.{action_name}'


def track_forum_event(request, event_name, course, obj, data, id_map=None):
    """
    Send out an analytics event when a forum event happens. Works for threads,
    responses to threads, and comments on those responses.
    """
    user = request.user
    data['id'] = obj.id
    commentable_id = data['commentable_id']

    team = get_team(commentable_id)
    if team is not None:
        data.update(team_id=team.team_id)

    if id_map is None:
        id_map = get_cached_discussion_id_map(course, [commentable_id], user)
    if commentable_id in id_map:
        data['category_name'] = id_map[commentable_id]["title"]
        data['category_id'] = commentable_id
    data['url'] = request.META.get('HTTP_REFERER', '')
    data['user_forums_roles'] = [
        role.name for role in user.roles.filter(course_id=course.id)
    ]
    data['user_course_roles'] = [
        role.role for role in user.courseaccessrole_set.filter(course_id=course.id)
    ]

    tracker.emit(event_name, data)


def track_created_event(request, event_name, course, obj, data):
    """
    Send analytics event for a newly created thread, response or comment.
    """
    if len(obj.body) > TRACKING_MAX_FORUM_BODY:
        data['truncated'] = True
    else:
        data['truncated'] = False
    data['body'] = obj.body[:TRACKING_MAX_FORUM_BODY]
    track_forum_event(request, event_name, course, obj, data)


def track_thread_created_event(request, course, thread, followed):
    """
    Send analytics event for a newly created thread.
    """
    event_name = _EVENT_NAME_TEMPLATE.format(obj_type='thread', action_name='created')
    event_data = {
        'commentable_id': thread.commentable_id,
        'group_id': thread.get("group_id"),
        'thread_type': thread.thread_type,
        'title': thread.title,
        'anonymous': thread.anonymous,
        'anonymous_to_peers': thread.anonymous_to_peers,
        'options': {'followed': followed},
        # There is a stated desire for an 'origin' property that will state
        # whether this thread was created via courseware or the forum.
        # However, the view does not contain that data, and including it will
        # likely require changes elsewhere.
    }
    track_created_event(request, event_name, course, thread, event_data)


def track_comment_created_event(request, course, comment, commentable_id, followed):
    """
    Send analytics event for a newly created response or comment.
    """
    obj_type = 'comment' if comment.get("parent_id") else 'response'
    event_name = _EVENT_NAME_TEMPLATE.format(obj_type=obj_type, action_name='created')
    event_data = {
        'discussion': {'id': comment.thread_id},
        'commentable_id': commentable_id,
        'options': {'followed': followed},
    }
    parent_id = comment.get('parent_id')
    if parent_id:
        event_data['response'] = {'id': parent_id}
    track_created_event(request, event_name, course, comment, event_data)


def track_voted_event(request, course, obj, vote_value, undo_vote=False):
    """
    Send analytics event for a vote on a thread or response.
    """
    if isinstance(obj, cc.Thread):
        obj_type = 'thread'
    else:
        obj_type = 'response'
    event_name = _EVENT_NAME_TEMPLATE.format(obj_type=obj_type, action_name='voted')
    event_data = {
        'commentable_id': obj.commentable_id,
        'target_username': obj.get('username'),
        'undo_vote': undo_vote,
        'vote_value': vote_value,
    }
    track_forum_event(request, event_name, course, obj, event_data)


def permitted(func):
    """
    View decorator to verify the user is authorized to access this endpoint.
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        """
        Wrapper for the view that only calls the view if the user is authorized.
        """
        def fetch_content():
            """
            Extract the forum object from the keyword arguments to the view.
            """
            if "thread_id" in kwargs:
                content = cc.Thread.find(kwargs["thread_id"]).to_dict()
            elif "comment_id" in kwargs:
                content = cc.Comment.find(kwargs["comment_id"]).to_dict()
            elif "commentable_id" in kwargs:
                content = cc.Commentable.find(kwargs["commentable_id"]).to_dict()
            else:
                content = None
            return content
        course_key = CourseKey.from_string(kwargs['course_id'])
        if check_permissions_by_view(request.user, course_key, fetch_content(), request.view_name):
            return func(request, *args, **kwargs)
        else:
            return JsonError("unauthorized", status=401)
    return wrapper


def ajax_content_response(request, course_key, content):
    """
    Standard AJAX response returning the content hierarchy of the current thread.
    """
    user_info = cc.User.from_django_user(request.user).to_dict()
    annotated_content_info = get_annotated_content_info(course_key, content, request.user, user_info)
    return JsonResponse({
        'content': prepare_content(content, course_key),
        'annotated_content_info': annotated_content_info,
    })


def _get_excerpt(body, max_len=None):
    """
    Returns an excerpt from a discussion item body
    """

    if not max_len:
        max_len = getattr(settings, 'NOTIFICATIONS_MAX_EXCERPT_LEN', 65)

    excerpt = strip_tags(body).replace('\n', '').replace('\r', '')
    if len(excerpt) > max_len:
        excerpt = '{}...'.format(excerpt[:max_len])
    return excerpt


@require_POST
@login_required
@permitted
def create_thread(request, course_id, commentable_id):
    """
    Given a course and commentble ID, create the thread
    """

    log.debug("Creating new thread in %r, id %r", course_id, commentable_id)
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)
    post = request.POST
    user = request.user

    if course.allow_anonymous:
        anonymous = post.get('anonymous', 'false').lower() == 'true'
    else:
        anonymous = False

    if course.allow_anonymous_to_peers:
        anonymous_to_peers = post.get('anonymous_to_peers', 'false').lower() == 'true'
    else:
        anonymous_to_peers = False

    if 'title' not in post or not post['title'].strip():
        return JsonError(_("Title can't be empty"))
    if 'body' not in post or not post['body'].strip():
        return JsonError(_("Body can't be empty"))

    params = {
        'anonymous': anonymous,
        'anonymous_to_peers': anonymous_to_peers,
        'commentable_id': commentable_id,
        'course_id': course_key.to_deprecated_string(),
        'user_id': user.id,
        'thread_type': post["thread_type"],
        'body': post["body"],
        'title': post["title"],
    }

    # Check for whether this commentable belongs to a team, and add the right context
    if get_team(commentable_id) is not None:
        params['context'] = ThreadContext.STANDALONE
    else:
        params['context'] = ThreadContext.COURSE

    thread = cc.Thread(**params)

    # Cohort the thread if required
    try:
        group_id = get_group_id_for_comments_service(request, course_key, commentable_id)
    except ValueError:
        return HttpResponseBadRequest("Invalid cohort id")
    if group_id is not None:
        thread.group_id = group_id

    thread.save()

    thread_created.send(sender=None, user=user, post=thread)

    # patch for backward compatibility to comments service
    if 'pinned' not in thread.attributes:
        thread['pinned'] = False

    follow = post.get('auto_subscribe', 'false').lower() == 'true'

    if follow:
        cc_user = cc.User.from_django_user(user)
        cc_user.follow(thread)

    data = thread.to_dict()

    add_courseware_context([data], course, user)

    track_thread_created_event(request, course, thread, follow)

    if thread.get('group_id'):
        # Send a notification message, if enabled, when anyone posts a new thread on
        # a cohorted/private discussion, except the poster him/herself
        _send_discussion_notification(
            'open-edx.lms.discussions.cohorted-thread-added',
            unicode(course_key),
            thread,
            request.user,
            excerpt=_get_excerpt(thread.body),
            recipient_group_id=thread.get('group_id'),
            recipient_exclude_user_ids=[request.user.id],
            is_anonymous_user=anonymous or anonymous_to_peers
        )

    # call into the social_engagement django app to
    # rescore this user
    _update_user_engagement_score(course_key, request.user.id)

    add_courseware_context([data], course, user)
    add_thread_group_name(data, course_key)
    add_courseware_context([data], course)
    if request.is_ajax():
        return ajax_content_response(request, course_key, data)
    else:
        return JsonResponse(prepare_content(data, course_key))


def _send_discussion_notification(
    type_name,
    course_id,
    thread,
    request_user,
    excerpt=None,
    recipient_user_id=None,
    recipient_group_id=None,
    recipient_exclude_user_ids=None,
    extra_payload=None,
    is_anonymous_user=False
):
    """
    Helper method to consolidate Notification trigger workflow
    """
    try:
        # is Notifications feature enabled?
        if not settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):
            return

        if is_anonymous_user:
            action_username = _('An anonymous user')
        else:
            action_username = request_user.username

        # get the notification type.
        msg = NotificationMessage(
            msg_type=get_notification_type(type_name),
            namespace=course_id,
            # base payload, other values will be passed in as extra_payload
            payload={
                '_schema_version': '1',
                'action_username': action_username,
                'thread_title': thread.title,
            }
        )

        # add in additional payload info
        # that might be type specific
        if extra_payload:
            msg.payload.update(extra_payload)

        if excerpt:
            msg.payload.update({
                'excerpt': excerpt,
            })

        # Add information so that we can resolve
        # click through links in the Notification
        # rendering, typically this will be used
        # to bring the user back to this part of
        # the discussion forum

        #
        # IMPORTANT: This can be changed to msg.add_click_link() if we
        # have a URL that we wish to use. In the initial use case,
        # we need to make the link point to a different front end
        #
        msg.add_click_link_params({
            'course_id': course_id,
            'commentable_id': thread.commentable_id,
            'thread_id': thread.id,
        })

        if recipient_user_id:
            # send notification to single user
            publish_notification_to_user(recipient_user_id, msg)

        if recipient_group_id:
            # Send the notification_msg to the CourseGroup via Celery
            # But we can also exclude some users from that list
            if settings.FEATURES.get('ENABLE_NOTIFICATIONS_CELERY', False):
                publish_course_group_notification_task.delay(
                    recipient_group_id,
                    msg,
                    exclude_user_ids=recipient_exclude_user_ids
                )
            else:
                publish_course_group_notification_task(
                    recipient_group_id,
                    msg,
                    exclude_user_ids=recipient_exclude_user_ids
                )
    except Exception, ex:
        # Notifications are never critical, so we don't want to disrupt any
        # other logic processing. So log and continue.
        log.exception(ex)

@require_POST
@login_required
@permitted
def update_thread(request, course_id, thread_id):
    """
    Given a course id and thread id, update a existing thread, used for both static and ajax submissions
    """
    if 'title' not in request.POST or not request.POST['title'].strip():
        return JsonError(_("Title can't be empty"))
    if 'body' not in request.POST or not request.POST['body'].strip():
        return JsonError(_("Body can't be empty"))

    course_key = CourseKey.from_string(course_id)
    thread = cc.Thread.find(thread_id)
    # Get thread context first in order to be safe from reseting the values of thread object later
    thread_context = getattr(thread, "context", "course")
    thread.body = request.POST["body"]
    thread.title = request.POST["title"]
    user = request.user
    # The following checks should avoid issues we've seen during deploys, where end users are hitting an updated server
    # while their browser still has the old client code. This will avoid erasing present values in those cases.
    if "thread_type" in request.POST:
        thread.thread_type = request.POST["thread_type"]
    if "commentable_id" in request.POST:
        commentable_id = request.POST["commentable_id"]
        course = get_course_with_access(user, 'load', course_key)
        if thread_context == "course" and not discussion_category_id_access(course, user, commentable_id):
            return JsonError(_("Topic doesn't exist"))
        else:
            thread.commentable_id = commentable_id

    thread.save()

    thread_edited.send(sender=None, user=user, post=thread)

    if request.is_ajax():
        return ajax_content_response(request, course_key, thread.to_dict())
    else:
        return JsonResponse(prepare_content(thread.to_dict(), course_key))


def _create_comment(request, course_key, thread_id=None, parent_id=None):
    """
    given a course_key, thread_id, and parent_id, create a comment,
    called from create_comment to do the actual creation
    """
    assert isinstance(course_key, CourseKey)
    post = request.POST
    user = request.user

    if 'body' not in post or not post['body'].strip():
        return JsonError(_("Body can't be empty"))

    course = get_course_with_access(user, 'load', course_key)
    if course.allow_anonymous:
        anonymous = post.get('anonymous', 'false').lower() == 'true'
    else:
        anonymous = False

    if course.allow_anonymous_to_peers:
        anonymous_to_peers = post.get('anonymous_to_peers', 'false').lower() == 'true'
    else:
        anonymous_to_peers = False

    comment = cc.Comment(
        anonymous=anonymous,
        anonymous_to_peers=anonymous_to_peers,
        user_id=user.id,
        course_id=course_key.to_deprecated_string(),
        thread_id=thread_id,
        parent_id=parent_id,
        body=post["body"]
    )
    comment.save()

    comment_created.send(sender=None, user=user, post=comment)

    followed = post.get('auto_subscribe', 'false').lower() == 'true'

    if followed:
        cc_user = cc.User.from_django_user(request.user)
        cc_user.follow(comment.thread)

    track_comment_created_event(request, course, comment, comment.thread.commentable_id, followed)

    # Update social stats
    #
    # NOTE: We do a check for NOTIFICATIONS enablement, because we
    # need some of the variables (e.g. replying_to_id) below to be set
    #
    if settings.FEATURES.get("ENABLE_SOCIAL_ENGAGEMENT", False) or settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):
        # call into the social_engagement django app to
        # rescore this user who created the comment
        _update_user_engagement_score(course_key, request.user.id)

        # a response is a reply to a thread
        # a comment is a reply to a response
        is_comment = not thread_id and parent_id

        replying_to_id = None  # keep track of who we are replying to
        if is_comment:
            # If creating a comment, then we don't have the original thread_id
            # so we have to get it from the parent
            comment = cc.Comment.find(parent_id)
            thread_id = comment.thread_id
            replying_to_id = comment.user_id

            # update the engagement of the author of the response
            _update_user_engagement_score(course_key, replying_to_id)

        thread = cc.Thread.find(thread_id)

        # IMPORTANT: we have to use getattr here as
        # otherwise the property will not get fetched
        # from cs_comment_service
        thread_user_id = int(getattr(thread, 'user_id', 0))

        # update the engagement score of the thread creator
        # as well
        _update_user_engagement_score(course_key, thread_user_id)

    #
    # Send notification
    #
    # Feature Flag to check that notifications are enabled or not.
    if settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):

        action_user_id = request.user.id

        if not replying_to_id:
            # we must be creating a Reponse on a thread,
            # so the original poster is the author of the thread
            replying_to_id =thread_user_id

        #
        # IMPORTANT: We have to use getattr() here so that the
        # object is fully hydrated. This is a known limitation.
        #
        group_id = getattr(thread, 'group_id')

        if group_id:
            # We always send a notification to the whole cohort
            # when someone posts a comment, except the poster

            _send_discussion_notification(
                'open-edx.lms.discussions.cohorted-comment-added',
                unicode(course_key),
                thread,
                request.user,
                excerpt=_get_excerpt(post["body"]),
                recipient_group_id=thread.get('group_id'),
                recipient_exclude_user_ids=[request.user.id],
                is_anonymous_user=anonymous or anonymous_to_peers
            )

        elif parent_id is None and action_user_id != replying_to_id:
            # we have to only send the notifications when
            # the user commenting the thread is not
            # the same user who created the thread
            # parent_id is None: publish notification only when creating the comment on
            # the thread not replying on the comment. When the user replied on the comment
            # the parent_id is not None at that time

            _send_discussion_notification(
                'open-edx.lms.discussions.reply-to-thread',
                unicode(course_key),
                thread,
                request.user,
                excerpt=_get_excerpt(post["body"]),
                recipient_user_id=replying_to_id,
                is_anonymous_user=anonymous or anonymous_to_peers
            )

    if request.is_ajax():
        return ajax_content_response(request, course_key, comment.to_dict())
    else:
        return JsonResponse(prepare_content(comment.to_dict(), course.id))


@require_POST
@login_required
@permitted
def create_comment(request, course_id, thread_id):
    """
    given a course_id and thread_id, test for comment depth. if not too deep,
    call _create_comment to create the actual comment.
    """
    if is_comment_too_deep(parent=None):
        return JsonError(_("Comment level too deep"))
    return _create_comment(request, CourseKey.from_string(course_id), thread_id=thread_id)


@require_POST
@login_required
@permitted
def delete_thread(request, course_id, thread_id):
    """
    given a course_id and thread_id, delete this thread
    this is ajax only
    """
    course_key = CourseKey.from_string(course_id)
    thread = cc.Thread.find(thread_id)
    thread.delete()
    thread_deleted.send(sender=None, user=request.user, post=thread)
    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def update_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id, update the comment with payload attributes
    handles static and ajax submissions
    """
    course_key = CourseKey.from_string(course_id)
    comment = cc.Comment.find(comment_id)
    if 'body' not in request.POST or not request.POST['body'].strip():
        return JsonError(_("Body can't be empty"))
    comment.body = request.POST["body"]
    comment.save()

    comment_edited.send(sender=None, user=request.user, post=comment)

    if request.is_ajax():
        return ajax_content_response(request, course_key, comment.to_dict())
    else:
        return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def endorse_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id, toggle the endorsement of this comment,
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    comment = cc.Comment.find(comment_id)
    user = request.user
    comment.endorsed = request.POST.get('endorsed', 'false').lower() == 'true'
    comment.endorsement_user_id = user.id
    comment.save()
    comment_endorsed.send(sender=None, user=user, post=comment)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def openclose_thread(request, course_id, thread_id):
    """
    given a course_id and thread_id, toggle the status of this thread
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    thread = cc.Thread.find(thread_id)
    thread.closed = request.POST.get('closed', 'false').lower() == 'true'
    thread.save()

    return JsonResponse({
        'content': prepare_content(thread.to_dict(), course_key),
        'ability': get_ability(course_key, thread.to_dict(), request.user),
    })


@require_POST
@login_required
@permitted
def create_sub_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id, create a response to a comment
    after checking the max depth allowed, if allowed
    """
    if is_comment_too_deep(parent=cc.Comment(comment_id)):
        return JsonError(_("Comment level too deep"))
    return _create_comment(request, CourseKey.from_string(course_id), parent_id=comment_id)


@require_POST
@login_required
@permitted
def delete_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id delete this comment
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    comment = cc.Comment.find(comment_id)
    comment.delete()
    comment_deleted.send(sender=None, user=request.user, post=comment)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


def _vote_or_unvote(request, course_id, obj, value='up', undo_vote=False):
    """
    Vote or unvote for a thread or a response.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)
    user = cc.User.from_django_user(request.user)
    if undo_vote:
        user.unvote(obj)
        # TODO(smarnach): Determine the value of the vote that is undone.  Currently, you can
        # only cast upvotes in the user interface, so it is assumed that the vote value is 'up'.
        # (People could theoretically downvote by handcrafting AJAX requests.)
    else:
        user.vote(obj, value)
    track_voted_event(request, course, obj, value, undo_vote)
    return JsonResponse(prepare_content(obj.to_dict(), course_key))


@require_POST
@login_required
@permitted
def vote_for_comment(request, course_id, comment_id, value):
    """
    Given a course_id and comment_id, vote for this response.  AJAX only.
    """
    comment = cc.Comment.find(comment_id)
    result = _vote_or_unvote(request, course_id, comment, value)
    comment_voted.send(sender=None, user=request.user, post=comment)

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    # Feature Flag to check that notifications are enabled or not.
    if value=='up' and settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):
        action_user_id = request.user.id
        original_poster_id = int(comment.user_id)

        thread = cc.Thread.find(comment.thread_id)

        # refetch the comment, so we have the updated counters

        comment = cc.Comment.find(comment_id)

        # we have to only send the notifications when
        # the user voting comment the comment is not
        # the same user who created the comment
        if action_user_id != original_poster_id:
            _send_discussion_notification(
                'open-edx.lms.discussions.comment-upvoted',
                unicode(course_key),
                thread,
                request.user,
                recipient_user_id=original_poster_id,
                extra_payload={
                    'num_upvotes': comment.votes['up_count'],
                }
            )

    if value=='up':
        # call into the social_engagement django app to
        # rescore this user
        _update_user_engagement_score(course_key, comment.user_id)

    return result


@require_POST
@login_required
@permitted
def undo_vote_for_comment(request, course_id, comment_id):
    """
    given a course id and comment id, remove vote
    ajax only
    """
    return _vote_or_unvote(request, course_id, cc.Comment.find(comment_id), undo_vote=True)


@require_POST
@login_required
@permitted
def vote_for_thread(request, course_id, thread_id, value):
    """
    given a course id and thread id vote for this thread
    ajax only
    """
    thread = cc.Thread.find(thread_id)
    result = _vote_or_unvote(request, course_id, thread, value)
    thread_voted.send(sender=None, user=request.user, post=thread)

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    # call into the social_engagement django app to
    # rescore this user
    _update_user_engagement_score(course_key, thread.user_id)

    # Feature Flag to check that notifications are enabled or not.
    if value=='up' and settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):
        action_user_id = request.user.id
        original_poster_id = int(thread.user_id)

        # refetch the thread to get updated count metrics
        thread = cc.Thread.find(thread_id)

        # we have to only send the notifications when
        # the user voting the thread is not
        # the same user who created the thread
        if action_user_id != original_poster_id:
            _send_discussion_notification(
                'open-edx.lms.discussions.post-upvoted',
                unicode(course_key),
                thread,
                request.user,
                recipient_user_id=original_poster_id,
                extra_payload={
                    'num_upvotes': thread.votes['up_count'],
                }
            )

    return result


@require_POST
@login_required
@permitted
def undo_vote_for_thread(request, course_id, thread_id):
    """
    given a course id and thread id, remove users vote for thread
    ajax only
    """
    return _vote_or_unvote(request, course_id, cc.Thread.find(thread_id), undo_vote=True)


@require_POST
@login_required
@permitted
def flag_abuse_for_thread(request, course_id, thread_id):
    """
    given a course_id and thread_id flag this thread for abuse
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    thread.flagAbuse(user, thread)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def un_flag_abuse_for_thread(request, course_id, thread_id):
    """
    given a course id and thread id, remove abuse flag for this thread
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    thread = cc.Thread.find(thread_id)
    remove_all = bool(
        has_permission(request.user, 'openclose_thread', course_key) or
        has_access(request.user, 'staff', course)
    )
    thread.unFlagAbuse(user, thread, remove_all)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def flag_abuse_for_comment(request, course_id, comment_id):
    """
    given a course and comment id, flag comment for abuse
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    user = cc.User.from_django_user(request.user)
    comment = cc.Comment.find(comment_id)
    comment.flagAbuse(user, comment)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def un_flag_abuse_for_comment(request, course_id, comment_id):
    """
    given a course_id and comment id, unflag comment for abuse
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    remove_all = bool(
        has_permission(request.user, 'openclose_thread', course_key) or
        has_access(request.user, 'staff', course)
    )
    comment = cc.Comment.find(comment_id)
    comment.unFlagAbuse(user, comment, remove_all)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def pin_thread(request, course_id, thread_id):
    """
    given a course id and thread id, pin this thread
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    thread.pin(user, thread_id)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def un_pin_thread(request, course_id, thread_id):
    """
    given a course id and thread id, remove pin from this thread
    ajax only
    """
    course_key = CourseKey.from_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    thread.un_pin(user, thread_id)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def follow_thread(request, course_id, thread_id):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    user.follow(thread)

    # call into the social_engagement django app to
    # rescore this user
    _update_user_engagement_score(course_key, thread.user_id)

    # Feature Flag to check that notifications are enabled or not.
    if settings.FEATURES.get("ENABLE_NOTIFICATIONS", False):
        # only send notifications when the user
        # who is following the thread is not the same
        # who created the thread
        action_user_id = request.user.id
        original_poster_id = int(thread.user_id)

        # get number of followers
        try:
            num_followers = thread.get_num_followers()

            if original_poster_id != action_user_id:
                _send_discussion_notification(
                    'open-edx.lms.discussions.thread-followed',
                    unicode(course_key),
                    thread,
                    request.user,
                    recipient_user_id=original_poster_id,
                    extra_payload={
                        'num_followers': num_followers,
                    }
                )
        except Exception, ex:
            # sending notifications is not critical,
            # so log error and continue
            log.exception(ex)

    return JsonResponse({})


@require_POST
@login_required
@permitted
def follow_commentable(request, course_id, commentable_id):
    """
    given a course_id and commentable id, follow this commentable
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    commentable = cc.Commentable.find(commentable_id)
    user.follow(commentable)
    return JsonResponse({})


@require_POST
@login_required
@permitted
def unfollow_thread(request, course_id, thread_id):
    """
    given a course id and thread id, stop following this thread
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    user.unfollow(thread)
    return JsonResponse({})


@require_POST
@login_required
@permitted
def unfollow_commentable(request, course_id, commentable_id):
    """
    given a course id and commentable id stop following commentable
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    commentable = cc.Commentable.find(commentable_id)
    user.unfollow(commentable)
    return JsonResponse({})


@require_POST
@login_required
@csrf.csrf_exempt
def upload(request, course_id):  # ajax upload file to a question or answer
    """view that handles file upload via Ajax
    """

    # check upload permission
    error = ''
    new_file_name = ''
    try:
        # TODO authorization
        #may raise exceptions.PermissionDenied
        #if request.user.is_anonymous():
        #    msg = _('Sorry, anonymous users cannot upload files')
        #    raise exceptions.PermissionDenied(msg)

        #request.user.assert_can_upload_file()

        base_file_name = str(time.time()).replace('.', str(random.randint(0, 100000)))
        file_storage, new_file_name = store_uploaded_file(
            request, 'file-upload', cc_settings.ALLOWED_UPLOAD_FILE_TYPES, base_file_name,
            max_file_size=cc_settings.MAX_UPLOAD_FILE_SIZE
        )

    except exceptions.PermissionDenied, err:
        error = unicode(err)
    except Exception, err:
        print err
        logging.critical(unicode(err))
        error = _('Error uploading file. Please contact the site administrator. Thank you.')

    if error == '':
        result = _('Good')
        file_url = file_storage.url(new_file_name)
        parsed_url = urlparse.urlparse(file_url)
        file_url = urlparse.urlunparse(
            urlparse.ParseResult(
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                '', '', ''
            )
        )
    else:
        result = ''
        file_url = ''

    # Using content-type of text/plain here instead of JSON because
    # IE doesn't know how to handle the JSON response and prompts the
    # user to save the JSON as a file instead of passing it to the callback.
    return HttpResponse(json.dumps({
        'result': {
            'msg': result,
            'error': error,
            'file_url': file_url,
        }
    }), content_type="text/plain")


@require_GET
@login_required
def users(request, course_id):
    """
    Given a `username` query parameter, find matches for users in the forum for this course.

    Only exact matches are supported here, so the length of the result set will either be 0 or 1.
    """

    course_key = CourseKey.from_string(course_id)
    try:
        get_course_overview_with_access(request.user, 'load', course_key, check_if_enrolled=True)
    except Http404:
        # course didn't exist, or requesting user does not have access to it.
        return JsonError(status=404)

    try:
        username = request.GET['username']
    except KeyError:
        # 400 is default status for JsonError
        return JsonError(["username parameter is required"])

    user_objs = []
    try:
        matched_user = User.objects.get(username=username)
        cc_user = cc.User.from_django_user(matched_user)
        cc_user.course_id = course_key
        cc_user.retrieve(complete=False)
        if (cc_user['threads_count'] + cc_user['comments_count']) > 0:
            user_objs.append({
                'id': matched_user.id,
                'username': matched_user.username,
            })
    except User.DoesNotExist:
        pass
    return JsonResponse({"users": user_objs})


def _update_user_engagement_score(course_key, user_id):
    """
    Helper to call down into the Social Engagement app to recalc the passed in user's
    Social Engagement score
    """

    if settings.FEATURES.get('ENABLE_SOCIAL_ENGAGEMENT', False):
        update_user_engagement_score(course_key, user_id)
