import json
import logging
import xml.sax.saxutils as saxutils

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.contrib.auth.models import User
from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.http import require_GET
import newrelic.agent

from edxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from course_groups.cohorts import (is_course_cohorted, get_cohort_id, is_commentable_cohorted,
                                   get_cohorted_commentables, get_course_cohorts, get_cohort_by_id)
from courseware.access import has_access

from django_comment_client.permissions import cached_has_permission
from django_comment_client.utils import (
    merge_dict,
    extract,
    strip_none,
    add_courseware_context,
    add_thread_group_name,
    get_group_id_for_comments_service
)
import django_comment_client.utils as utils
import lms.lib.comment_client as cc

from opaque_keys.edx.locations import SlashSeparatedCourseKey

THREADS_PER_PAGE = 20
INLINE_THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2
log = logging.getLogger("edx.discussions")


def _attr_safe_json(obj):
    """
    return a JSON string for obj which is safe to embed as the value of an attribute in a DOM node
    """
    return saxutils.escape(json.dumps(obj), {'"': '&quot;'})

@newrelic.agent.function_trace()
def make_course_settings(course, include_category_map=False):
    """
    Generate a JSON-serializable model for course settings, which will be used to initialize a
    DiscussionCourseSettings object on the client.
    """

    obj = {
        'is_cohorted': is_course_cohorted(course.id),
        'allow_anonymous': course.allow_anonymous,
        'allow_anonymous_to_peers': course.allow_anonymous_to_peers,
        'cohorts': [{"id": str(g.id), "name": g.name} for g in get_course_cohorts(course.id)],
    }

    if include_category_map:
        obj['category_map'] = utils.get_discussion_category_map(course)

    return obj

@newrelic.agent.function_trace()
def get_threads(request, course_key, discussion_id=None, per_page=THREADS_PER_PAGE):
    """
    This may raise an appropriate subclass of cc.utils.CommentClientError
    if something goes wrong, or ValueError if the group_id is invalid.
    """
    default_query_params = {
        'page': 1,
        'per_page': per_page,
        'sort_key': 'date',
        'sort_order': 'desc',
        'text': '',
        'commentable_id': discussion_id,
        'course_id': course_key.to_deprecated_string(),
        'user_id': request.user.id,
        'group_id': get_group_id_for_comments_service(request, course_key, discussion_id),  # may raise ValueError
    }

    if not request.GET.get('sort_key'):
        # If the user did not select a sort key, use their last used sort key
        cc_user = cc.User.from_django_user(request.user)
        cc_user.retrieve()
        # TODO: After the comment service is updated this can just be user.default_sort_key because the service returns the default value
        default_query_params['sort_key'] = cc_user.get('default_sort_key') or default_query_params['sort_key']
    else:
        # If the user clicked a sort key, update their default sort key
        cc_user = cc.User.from_django_user(request.user)
        cc_user.default_sort_key = request.GET.get('sort_key')
        cc_user.save()

    #there are 2 dimensions to consider when executing a search with respect to group id
    #is user a moderator
    #did the user request a group

    query_params = merge_dict(
        default_query_params,
        strip_none(
            extract(
                request.GET,
                [
                    'page',
                    'sort_key',
                    'sort_order',
                    'text',
                    'commentable_ids',
                    'flagged',
                    'unread',
                    'unanswered',
                ]
            )
        )
    )

    threads, page, num_pages, corrected_text = cc.Thread.search(query_params)

    #now add the group name if the thread has a group id
    for thread in threads:
        add_thread_group_name(thread, course_key)

        #patch for backward compatibility to comments service
        if not 'pinned' in thread:
            thread['pinned'] = False

    query_params['page'] = page
    query_params['num_pages'] = num_pages
    query_params['corrected_text'] = corrected_text

    return threads, query_params


@login_required
def inline_discussion(request, course_id, discussion_id):
    """
    Renders JSON for DiscussionModules
    """
    nr_transaction = newrelic.agent.current_transaction()
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course = get_course_with_access(request.user, 'load_forum', course_id)
    cc_user = cc.User.from_django_user(request.user)
    user_info = cc_user.to_dict()

    try:
        threads, query_params = get_threads(request, course_id, discussion_id, per_page=INLINE_THREADS_PER_PAGE)
    except ValueError:
        return HttpResponseBadRequest("Invalid group_id")

    with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)
    is_staff = cached_has_permission(request.user, 'openclose_thread', course.id)
    return utils.JsonResponse({
        'discussion_data': [utils.safe_content(thread, course_id, is_staff) for thread in threads],
        'user_info': user_info,
        'annotated_content_info': annotated_content_info,
        'page': query_params['page'],
        'num_pages': query_params['num_pages'],
        'roles': utils.get_role_ids(course_id),
        'course_settings': make_course_settings(course)
    })

@login_required
def forum_form_discussion(request, course_id):
    """
    Renders the main Discussion page, potentially filtered by a search query
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    course = get_course_with_access(request.user, 'load_forum', course_id)
    course_settings = make_course_settings(course, include_category_map=True)

    user = cc.User.from_django_user(request.user)
    user_info = user.to_dict()

    try:
        unsafethreads, query_params = get_threads(request, course_id)   # This might process a search query
        is_staff = cached_has_permission(request.user, 'openclose_thread', course.id)
        threads = [utils.safe_content(thread, course_id, is_staff) for thread in unsafethreads]
    except cc.utils.CommentClientMaintenanceError:
        log.warning("Forum is in maintenance mode")
        return render_to_response('discussion/maintenance.html', {})
    except ValueError:
        return HttpResponseBadRequest("Invalid group_id")

    with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

    with newrelic.agent.FunctionTrace(nr_transaction, "add_courseware_context"):
        add_courseware_context(threads, course)

    if request.is_ajax():
        return utils.JsonResponse({
            'discussion_data': threads,   # TODO: Standardize on 'discussion_data' vs 'threads'
            'annotated_content_info': annotated_content_info,
            'num_pages': query_params['num_pages'],
            'page': query_params['page'],
            'corrected_text': query_params['corrected_text'],
        })
    else:
        with newrelic.agent.FunctionTrace(nr_transaction, "get_cohort_info"):
            user_cohort_id = get_cohort_id(request.user, course_id)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            #'recent_active_threads': recent_active_threads,
            'staff_access': has_access(request.user, 'staff', course),
            'threads': _attr_safe_json(threads),
            'thread_pages': query_params['num_pages'],
            'user_info': _attr_safe_json(user_info),
            'flag_moderator': cached_has_permission(request.user, 'openclose_thread', course.id) or has_access(request.user, 'staff', course),
            'annotated_content_info': _attr_safe_json(annotated_content_info),
            'course_id': course.id.to_deprecated_string(),
            'roles': _attr_safe_json(utils.get_role_ids(course_id)),
            'is_moderator': cached_has_permission(request.user, "see_all_cohorts", course_id),
            'cohorts': course_settings["cohorts"],  # still needed to render _thread_list_template
            'user_cohort': user_cohort_id, # read from container in NewPostView
            'is_course_cohorted': is_course_cohorted(course_id),  # still needed to render _thread_list_template
            'sort_preference': user.default_sort_key,
            'category_map': course_settings["category_map"],
            'course_settings': _attr_safe_json(course_settings)
        }
        # print "start rendering.."
        return render_to_response('discussion/index.html', context)


@require_GET
@login_required
def single_thread(request, course_id, discussion_id, thread_id):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    course = get_course_with_access(request.user, 'load_forum', course_key)
    course_settings = make_course_settings(course, include_category_map=True)
    cc_user = cc.User.from_django_user(request.user)
    user_info = cc_user.to_dict()
    is_moderator = cached_has_permission(request.user, "see_all_cohorts", course_key)

    # Currently, the front end always loads responses via AJAX, even for this
    # page; it would be a nice optimization to avoid that extra round trip to
    # the comments service.
    try:
        thread = cc.Thread.find(thread_id).retrieve(
            recursive=request.is_ajax(),
            user_id=request.user.id,
            response_skip=request.GET.get("resp_skip"),
            response_limit=request.GET.get("resp_limit")
        )
    except cc.utils.CommentClientRequestError as e:
        if e.status_code == 404:
            raise Http404
        raise

    # verify that the thread belongs to the requesting student's cohort
    if is_commentable_cohorted(course_key, discussion_id) and not is_moderator:
        user_group_id = get_cohort_id(request.user, course_key)
        if hasattr(thread, "group_id") and user_group_id != thread.group_id:
            raise Http404

    is_staff = cached_has_permission(request.user, 'openclose_thread', course.id)
    if request.is_ajax():
        with newrelic.agent.FunctionTrace(nr_transaction, "get_annotated_content_infos"):
            annotated_content_info = utils.get_annotated_content_infos(course_key, thread, request.user, user_info=user_info)
        content = utils.safe_content(thread.to_dict(), course_key, is_staff)
        add_thread_group_name(content, course_key)
        with newrelic.agent.FunctionTrace(nr_transaction, "add_courseware_context"):
            add_courseware_context([content], course)
        return utils.JsonResponse({
            'content': content,
            'annotated_content_info': annotated_content_info,
        })

    else:
        try:
            threads, query_params = get_threads(request, course_key)
        except ValueError:
            return HttpResponseBadRequest("Invalid group_id")
        threads.append(thread.to_dict())

        with newrelic.agent.FunctionTrace(nr_transaction, "add_courseware_context"):
            add_courseware_context(threads, course)

        for thread in threads:
            add_thread_group_name(thread, course_key)

            #patch for backward compatibility with comments service
            if not "pinned" in thread:
                thread["pinned"] = False

        threads = [utils.safe_content(thread, course_key, is_staff) for thread in threads]

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_key, threads, request.user, user_info)

        with newrelic.agent.FunctionTrace(nr_transaction, "get_cohort_info"):
            user_cohort = get_cohort_id(request.user, course_key)

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',   # TODO: What is this?
            'user_info': _attr_safe_json(user_info),
            'annotated_content_info': _attr_safe_json(annotated_content_info),
            'course': course,
            #'recent_active_threads': recent_active_threads,
            'course_id': course.id.to_deprecated_string(),   # TODO: Why pass both course and course.id to template?
            'thread_id': thread_id,
            'threads': _attr_safe_json(threads),
            'roles': _attr_safe_json(utils.get_role_ids(course_key)),
            'is_moderator': is_moderator,
            'thread_pages': query_params['num_pages'],
            'is_course_cohorted': is_course_cohorted(course_key),
            'flag_moderator': cached_has_permission(request.user, 'openclose_thread', course.id) or has_access(request.user, 'staff', course),
            'cohorts': course_settings["cohorts"],
            'user_cohort': user_cohort,
            'sort_preference': cc_user.default_sort_key,
            'category_map': course_settings["category_map"],
            'course_settings': _attr_safe_json(course_settings)
        }
        return render_to_response('discussion/index.html', context)

@require_GET
@login_required
def user_profile(request, course_id, user_id):
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    #TODO: Allow sorting?
    course = get_course_with_access(request.user, 'load_forum', course_id)
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE,   # more than threads_per_page to show more activities
        }

        try:
            group_id = get_group_id_for_comments_service(request, course_id)
        except ValueError:
            return HttpResponseBadRequest("Invalid group_id")
        if group_id is not None:
            query_params['group_id'] = group_id

        threads, page, num_pages = profiled_user.active_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

        if request.is_ajax():
            is_staff = cached_has_permission(request.user, 'openclose_thread', course.id)
            return utils.JsonResponse({
                'discussion_data': [utils.safe_content(thread, course_id, is_staff) for thread in threads],
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
                'annotated_content_info': _attr_safe_json(annotated_content_info),
            })
        else:
            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'threads': _attr_safe_json(threads),
                'user_info': _attr_safe_json(user_info),
                'annotated_content_info': _attr_safe_json(annotated_content_info),
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
#                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except User.DoesNotExist:
        raise Http404


@login_required
def followed_threads(request, course_id, user_id):
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    course = get_course_with_access(request.user, 'load_forum', course_id)
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        default_query_params = {
            'page': 1,
            'per_page': THREADS_PER_PAGE,   # more than threads_per_page to show more activities
            'sort_key': 'date',
            'sort_order': 'desc',
        }

        query_params = merge_dict(
            default_query_params,
            strip_none(
                extract(
                    request.GET,
                    [
                        'page',
                        'sort_key',
                        'sort_order',
                        'flagged',
                        'unread',
                        'unanswered',
                    ]
                )
            )
        )

        try:
            group_id = get_group_id_for_comments_service(request, course_id)
        except ValueError:
            return HttpResponseBadRequest("Invalid group_id")
        if group_id is not None:
            query_params['group_id'] = group_id

        threads, page, num_pages = profiled_user.subscribed_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)
        if request.is_ajax():
            is_staff = cached_has_permission(request.user, 'openclose_thread', course.id)
            return utils.JsonResponse({
                'annotated_content_info': annotated_content_info,
                'discussion_data': [utils.safe_content(thread, course_id, is_staff) for thread in threads],
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
            })
        else:

            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'threads': _attr_safe_json(threads),
                'user_info': _attr_safe_json(user_info),
                'annotated_content_info': _attr_safe_json(annotated_content_info),
                #                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except User.DoesNotExist:
        raise Http404
