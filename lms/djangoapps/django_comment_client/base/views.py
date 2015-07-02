import functools
import logging
import random
import time
import urlparse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import exceptions
from django.http import Http404, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from django.views.decorators import csrf
from django.views.decorators.http import require_GET, require_POST
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.access import has_access
from util.file import store_uploaded_file
from courseware.courses import get_course_with_access, get_course_by_id
import django_comment_client.settings as cc_settings
from django_comment_client.utils import (
    add_courseware_context,
    get_annotated_content_info,
    get_ability,
    is_comment_too_deep,
    JsonError,
    JsonResponse,
    prepare_content,
    get_group_id_for_comments_service,
    get_discussion_categories_ids,
    get_discussion_id_map,
)
from django_comment_client.permissions import check_permissions_by_view, has_permission
from eventtracking import tracker
import lms.lib.comment_client as cc

log = logging.getLogger(__name__)

TRACKING_MAX_FORUM_BODY = 2000

THREAD_CREATED_EVENT_NAME = "edx.forum.thread.created"
RESPONSE_CREATED_EVENT_NAME = 'edx.forum.response.created'
COMMENT_CREATED_EVENT_NAME = 'edx.forum.comment.created'


def permitted(fn):
    @functools.wraps(fn)
    def wrapper(request, *args, **kwargs):
        def fetch_content():
            if "thread_id" in kwargs:
                content = cc.Thread.find(kwargs["thread_id"]).to_dict()
            elif "comment_id" in kwargs:
                content = cc.Comment.find(kwargs["comment_id"]).to_dict()
            else:
                content = None
            return content
        course_key = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        if check_permissions_by_view(request.user, course_key, fetch_content(), request.view_name):
            return fn(request, *args, **kwargs)
        else:
            return JsonError("unauthorized", status=401)
    return wrapper


def ajax_content_response(request, course_key, content):
    user_info = cc.User.from_django_user(request.user).to_dict()
    annotated_content_info = get_annotated_content_info(course_key, content, request.user, user_info)
    return JsonResponse({
        'content': prepare_content(content, course_key),
        'annotated_content_info': annotated_content_info,
    })


def track_forum_event(request, event_name, course, obj, data, id_map=None):
    """
    Send out an analytics event when a forum event happens. Works for threads,
    responses to threads, and comments on those responses.
    """
    user = request.user
    data['id'] = obj.id
    if id_map is None:
        id_map = get_discussion_id_map(course, user)

    commentable_id = data['commentable_id']
    if commentable_id in id_map:
        data['category_name'] = id_map[commentable_id]["title"]
        data['category_id'] = commentable_id
    if len(obj.body) > TRACKING_MAX_FORUM_BODY:
        data['truncated'] = True
    else:
        data['truncated'] = False

    data['body'] = obj.body[:TRACKING_MAX_FORUM_BODY]
    data['url'] = request.META.get('HTTP_REFERER', '')
    data['user_forums_roles'] = [
        role.name for role in user.roles.filter(course_id=course.id)
    ]
    data['user_course_roles'] = [
        role.role for role in user.courseaccessrole_set.filter(course_id=course.id)
    ]

    tracker.emit(event_name, data)


def get_thread_created_event_data(thread, followed):
    """
    Get the event data payload for thread creation (excluding fields populated
    by track_forum_event)
    """
    return {
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


def get_comment_created_event_name(comment):
    """Get the appropriate event name for creating a response/comment"""
    return COMMENT_CREATED_EVENT_NAME if comment.get("parent_id") else RESPONSE_CREATED_EVENT_NAME


def get_comment_created_event_data(comment, commentable_id, followed):
    """
    Get the event data payload for comment creation (excluding fields populated
    by track_forum_event)
    """
    event_data = {
        'discussion': {'id': comment.thread_id},
        'commentable_id': commentable_id,
        'options': {'followed': followed},
    }

    parent_id = comment.get("parent_id")
    if parent_id:
        event_data['response'] = {'id': parent_id}

    return event_data


@require_POST
@login_required
@permitted
def create_thread(request, course_id, commentable_id):
    """
    Given a course and commentble ID, create the thread
    """

    log.debug("Creating new thread in %r, id %r", course_id, commentable_id)
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_with_access(request.user, 'load', course_key)
    post = request.POST

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

    thread = cc.Thread(
        anonymous=anonymous,
        anonymous_to_peers=anonymous_to_peers,
        commentable_id=commentable_id,
        course_id=course_key.to_deprecated_string(),
        user_id=request.user.id,
        thread_type=post["thread_type"],
        body=post["body"],
        title=post["title"]
    )

    # Cohort the thread if required
    try:
        group_id = get_group_id_for_comments_service(request, course_key, commentable_id)
    except ValueError:
        return HttpResponseBadRequest("Invalid cohort id")
    if group_id is not None:
        thread.group_id = group_id

    thread.save()

    # patch for backward compatibility to comments service
    if 'pinned' not in thread.attributes:
        thread['pinned'] = False

    follow = post.get('auto_subscribe', 'false').lower() == 'true'

    if follow:
        user = cc.User.from_django_user(request.user)
        user.follow(thread)

    event_data = get_thread_created_event_data(thread, follow)
    data = thread.to_dict()

    # Calls to id map are expensive, but we need this more than once.
    # Prefetch it.
    id_map = get_discussion_id_map(course, request.user)

    add_courseware_context([data], course, request.user, id_map=id_map)

    track_forum_event(request, THREAD_CREATED_EVENT_NAME,
                      course, thread, event_data, id_map=id_map)

    if request.is_ajax():
        return ajax_content_response(request, course_key, data)
    else:
        return JsonResponse(prepare_content(data, course_key))


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

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    thread = cc.Thread.find(thread_id)
    thread.body = request.POST["body"]
    thread.title = request.POST["title"]
    # The following checks should avoid issues we've seen during deploys, where end users are hitting an updated server
    # while their browser still has the old client code. This will avoid erasing present values in those cases.
    if "thread_type" in request.POST:
        thread.thread_type = request.POST["thread_type"]
    if "commentable_id" in request.POST:
        course = get_course_with_access(request.user, 'load', course_key)
        commentable_ids = get_discussion_categories_ids(course, request.user)
        if request.POST.get("commentable_id") in commentable_ids:
            thread.commentable_id = request.POST["commentable_id"]
        else:
            return JsonError(_("Topic doesn't exist"))

    thread.save()
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

    if 'body' not in post or not post['body'].strip():
        return JsonError(_("Body can't be empty"))

    course = get_course_with_access(request.user, 'load', course_key)
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
        user_id=request.user.id,
        course_id=course_key.to_deprecated_string(),
        thread_id=thread_id,
        parent_id=parent_id,
        body=post["body"]
    )
    comment.save()

    followed = post.get('auto_subscribe', 'false').lower() == 'true'

    if followed:
        user = cc.User.from_django_user(request.user)
        user.follow(comment.thread)

    event_name = get_comment_created_event_name(comment)
    event_data = get_comment_created_event_data(comment, comment.thread.commentable_id, followed)
    track_forum_event(request, event_name, course, comment, event_data)

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
    return _create_comment(request, SlashSeparatedCourseKey.from_deprecated_string(course_id), thread_id=thread_id)


@require_POST
@login_required
@permitted
def delete_thread(request, course_id, thread_id):  # pylint: disable=unused-argument
    """
    given a course_id and thread_id, delete this thread
    this is ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    thread = cc.Thread.find(thread_id)
    thread.delete()

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def update_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id, update the comment with payload attributes
    handles static and ajax submissions
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    comment = cc.Comment.find(comment_id)
    if 'body' not in request.POST or not request.POST['body'].strip():
        return JsonError(_("Body can't be empty"))
    comment.body = request.POST["body"]
    comment.save()
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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    comment = cc.Comment.find(comment_id)
    comment.endorsed = request.POST.get('endorsed', 'false').lower() == 'true'
    comment.endorsement_user_id = request.user.id
    comment.save()
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def openclose_thread(request, course_id, thread_id):
    """
    given a course_id and thread_id, toggle the status of this thread
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
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
    return _create_comment(request, SlashSeparatedCourseKey.from_deprecated_string(course_id), parent_id=comment_id)


@require_POST
@login_required
@permitted
def delete_comment(request, course_id, comment_id):
    """
    given a course_id and comment_id delete this comment
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    comment = cc.Comment.find(comment_id)
    comment.delete()
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def vote_for_comment(request, course_id, comment_id, value):
    """
    given a course_id and comment_id,
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    comment = cc.Comment.find(comment_id)
    user.vote(comment, value)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def undo_vote_for_comment(request, course_id, comment_id):
    """
    given a course id and comment id, remove vote
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    comment = cc.Comment.find(comment_id)
    user.unvote(comment)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def vote_for_thread(request, course_id, thread_id, value):
    """
    given a course id and thread id vote for this thread
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    user.vote(thread, value)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def flag_abuse_for_thread(request, course_id, thread_id):
    """
    given a course_id and thread_id flag this thread for abuse
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_key)
    thread = cc.Thread.find(thread_id)
    remove_all = (
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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_key)
    remove_all = (
        has_permission(request.user, 'openclose_thread', course_key) or
        has_access(request.user, 'staff', course)
    )
    comment = cc.Comment.find(comment_id)
    comment.unFlagAbuse(user, comment, remove_all)
    return JsonResponse(prepare_content(comment.to_dict(), course_key))


@require_POST
@login_required
@permitted
def undo_vote_for_thread(request, course_id, thread_id):
    """
    given a course id and thread id, remove users vote for thread
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    user.unvote(thread)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def pin_thread(request, course_id, thread_id):
    """
    given a course id and thread id, pin this thread
    ajax only
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    thread.un_pin(user, thread_id)

    return JsonResponse(prepare_content(thread.to_dict(), course_key))


@require_POST
@login_required
@permitted
def follow_thread(request, course_id, thread_id):
    user = cc.User.from_django_user(request.user)
    thread = cc.Thread.find(thread_id)
    user.follow(thread)
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
def follow_user(request, course_id, followed_user_id):
    user = cc.User.from_django_user(request.user)
    followed_user = cc.User.find(followed_user_id)
    user.follow(followed_user)
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
@permitted
def unfollow_user(request, course_id, followed_user_id):
    """
    given a course id and user id, stop following this user
    ajax only
    """
    user = cc.User.from_django_user(request.user)
    followed_user = cc.User.find(followed_user_id)
    user.unfollow(followed_user)
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

    return JsonResponse({
        'result': {
            'msg': result,
            'error': error,
            'file_url': file_url,
        }
    })


@require_GET
@login_required
def users(request, course_id):
    """
    Given a `username` query parameter, find matches for users in the forum for this course.

    Only exact matches are supported here, so the length of the result set will either be 0 or 1.
    """

    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
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
