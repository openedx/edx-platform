import json
import logging
import xml.sax.saxutils as saxutils

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.contrib.auth.models import User
from django.http import Http404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET
import newrelic.agent

from edxmako.shortcuts import render_to_response
from courseware.courses import get_course_with_access
from course_groups.cohorts import (is_course_cohorted, get_cohort_id, is_commentable_cohorted,
                                   get_cohorted_commentables, get_course_cohorts, get_cohort_by_id)
from courseware.access import has_access

from django_comment_client.permissions import cached_has_permission
from django_comment_client.utils import (merge_dict, extract, strip_none, add_courseware_context)
import django_comment_client.utils as utils
import lms.lib.comment_client as cc

from opaque_keys.edx.locations import SlashSeparatedCourseKey

THREADS_PER_PAGE = 20
INLINE_THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2
escapedict = {'"': '&quot;'}
log = logging.getLogger("edx.discussions")


@newrelic.agent.function_trace()
def get_threads(request, course_id, discussion_id=None, per_page=THREADS_PER_PAGE):
    """
    This may raise an appropriate subclass of cc.utils.CommentClientError
    if something goes wrong.
    """
    default_query_params = {
        'page': 1,
        'per_page': per_page,
        'sort_key': 'date',
        'sort_order': 'desc',
        'text': '',
        'commentable_id': discussion_id,
        'course_id': course_id.to_deprecated_string(),
        'user_id': request.user.id,
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

    #if the user requested a group explicitly, give them that group, othewrise, if mod, show all, else if student, use cohort

    group_id = request.GET.get('group_id')

    if group_id == "all":
        group_id = None

    if not group_id:
        if not cached_has_permission(request.user, "see_all_cohorts", course_id):
            group_id = get_cohort_id(request.user, course_id)

    if group_id:
        default_query_params["group_id"] = group_id

    #so by default, a moderator sees all items, and a student sees his cohort

    query_params = merge_dict(default_query_params,
                              strip_none(extract(request.GET,
                                                 ['page', 'sort_key',
                                                  'sort_order', 'text',
                                                  'commentable_ids', 'flagged'])))

    threads, page, num_pages, corrected_text = cc.Thread.search(query_params)

    #now add the group name if the thread has a group id
    for thread in threads:

        if thread.get('group_id'):
            thread['group_name'] = get_cohort_by_id(course_id, thread.get('group_id')).name
            thread['group_string'] = "This post visible only to Group %s." % (thread['group_name'])
        else:
            thread['group_name'] = ""
            thread['group_string'] = "This post visible to everyone."

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

    threads, query_params = get_threads(request, course_id, discussion_id, per_page=INLINE_THREADS_PER_PAGE)
    cc_user = cc.User.from_django_user(request.user)
    user_info = cc_user.to_dict()

    with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

    allow_anonymous = course.allow_anonymous
    allow_anonymous_to_peers = course.allow_anonymous_to_peers

    #since inline is all one commentable, only show or allow the choice of cohorts
    #if the commentable is cohorted, otherwise everything is not cohorted
    #and no one has the option of choosing a cohort
    is_cohorted = is_course_cohorted(course_id) and is_commentable_cohorted(course_id, discussion_id)
    is_moderator = cached_has_permission(request.user, "see_all_cohorts", course_id)

    cohorts_list = list()

    if is_cohorted:
        cohorts_list.append({'name': _('All Groups'), 'id': None})

        #if you're a mod, send all cohorts and let you pick

        if is_moderator:
            cohorts = get_course_cohorts(course_id)
            for cohort in cohorts:
                cohorts_list.append({'name': cohort.name, 'id': cohort.id})

        else:
            #students don't get to choose
            cohorts_list = None

    return utils.JsonResponse({
        'discussion_data': map(utils.safe_content, threads),
        'user_info': user_info,
        'annotated_content_info': annotated_content_info,
        'page': query_params['page'],
        'num_pages': query_params['num_pages'],
        'roles': utils.get_role_ids(course_id),
        'allow_anonymous_to_peers': allow_anonymous_to_peers,
        'allow_anonymous': allow_anonymous,
        'cohorts': cohorts_list,
        'is_moderator': is_moderator,
        'is_cohorted': is_cohorted
    })


@login_required
def forum_form_discussion(request, course_id):
    """
    Renders the main Discussion page, potentially filtered by a search query
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    course = get_course_with_access(request.user, 'load_forum', course_id)
    with newrelic.agent.FunctionTrace(nr_transaction, "get_discussion_category_map"):
        category_map = utils.get_discussion_category_map(course)

    try:
        unsafethreads, query_params = get_threads(request, course_id)   # This might process a search query
        threads = [utils.safe_content(thread) for thread in unsafethreads]
    except cc.utils.CommentClientMaintenanceError:
        log.warning("Forum is in maintenance mode")
        return render_to_response('discussion/maintenance.html', {})

    user = cc.User.from_django_user(request.user)
    user_info = user.to_dict()

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
            cohorts = get_course_cohorts(course_id)
            cohorted_commentables = get_cohorted_commentables(course_id)

            user_cohort_id = get_cohort_id(request.user, course_id)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            #'recent_active_threads': recent_active_threads,
            'staff_access': has_access(request.user, 'staff', course),
            'threads': saxutils.escape(json.dumps(threads), escapedict),
            'thread_pages': query_params['num_pages'],
            'user_info': saxutils.escape(json.dumps(user_info), escapedict),
            'flag_moderator': cached_has_permission(request.user, 'openclose_thread', course.id) or has_access(request.user, 'staff', course),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            'course_id': course.id.to_deprecated_string(),
            'category_map': category_map,
            'roles': saxutils.escape(json.dumps(utils.get_role_ids(course_id)), escapedict),
            'is_moderator': cached_has_permission(request.user, "see_all_cohorts", course_id),
            'cohorts': cohorts,
            'user_cohort': user_cohort_id,
            'cohorted_commentables': cohorted_commentables,
            'is_course_cohorted': is_course_cohorted(course_id),
            'sort_preference': user.default_sort_key,
        }
        # print "start rendering.."
        return render_to_response('discussion/index.html', context)


@require_GET
@login_required
def single_thread(request, course_id, discussion_id, thread_id):
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    nr_transaction = newrelic.agent.current_transaction()

    course = get_course_with_access(request.user, 'load_forum', course_id)
    cc_user = cc.User.from_django_user(request.user)
    user_info = cc_user.to_dict()

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

    if request.is_ajax():
        with newrelic.agent.FunctionTrace(nr_transaction, "get_annotated_content_infos"):
            annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, user_info=user_info)
        content = utils.safe_content(thread.to_dict())
        with newrelic.agent.FunctionTrace(nr_transaction, "add_courseware_context"):
            add_courseware_context([content], course)
        return utils.JsonResponse({
            'content': content,
            'annotated_content_info': annotated_content_info,
        })

    else:
        with newrelic.agent.FunctionTrace(nr_transaction, "get_discussion_category_map"):
            category_map = utils.get_discussion_category_map(course)

        threads, query_params = get_threads(request, course_id)
        threads.append(thread.to_dict())

        course = get_course_with_access(request.user, 'load_forum', course_id)

        with newrelic.agent.FunctionTrace(nr_transaction, "add_courseware_context"):
            add_courseware_context(threads, course)

        for thread in threads:
            if thread.get('group_id') and not thread.get('group_name'):
                thread['group_name'] = get_cohort_by_id(course_id, thread.get('group_id')).name

            #patch for backward compatibility with comments service
            if not "pinned" in thread:
                thread["pinned"] = False

        threads = [utils.safe_content(thread) for thread in threads]

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

        with newrelic.agent.FunctionTrace(nr_transaction, "get_cohort_info"):
            cohorts = get_course_cohorts(course_id)
            cohorted_commentables = get_cohorted_commentables(course_id)
            user_cohort = get_cohort_id(request.user, course_id)
        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',   # TODO: What is this?
            'user_info': saxutils.escape(json.dumps(user_info), escapedict),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            'course': course,
            #'recent_active_threads': recent_active_threads,
            'course_id': course.id.to_deprecated_string(),   # TODO: Why pass both course and course.id to template?
            'thread_id': thread_id,
            'threads': saxutils.escape(json.dumps(threads), escapedict),
            'category_map': category_map,
            'roles': saxutils.escape(json.dumps(utils.get_role_ids(course_id)), escapedict),
            'thread_pages': query_params['num_pages'],
            'is_course_cohorted': is_course_cohorted(course_id),
            'is_moderator': cached_has_permission(request.user, "see_all_cohorts", course_id),
            'flag_moderator': cached_has_permission(request.user, 'openclose_thread', course.id) or has_access(request.user, 'staff', course),
            'cohorts': cohorts,
            'user_cohort': get_cohort_id(request.user, course_id),
            'cohorted_commentables': cohorted_commentables,
            'sort_preference': cc_user.default_sort_key,
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

        threads, page, num_pages = profiled_user.active_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

        if request.is_ajax():
            return utils.JsonResponse({
                'discussion_data': map(utils.safe_content, threads),
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            })
        else:
            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'threads': saxutils.escape(json.dumps(threads), escapedict),
                'user_info': saxutils.escape(json.dumps(user_info), escapedict),
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
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

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE,   # more than threads_per_page to show more activities
            'sort_key': request.GET.get('sort_key', 'date'),
            'sort_order': request.GET.get('sort_order', 'desc'),
        }

        threads, page, num_pages = profiled_user.subscribed_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

        with newrelic.agent.FunctionTrace(nr_transaction, "get_metadata_for_threads"):
            annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)
        if request.is_ajax():
            return utils.JsonResponse({
                'annotated_content_info': annotated_content_info,
                'discussion_data': map(utils.safe_content, threads),
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
            })
        else:

            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'threads': saxutils.escape(json.dumps(threads), escapedict),
                'user_info': saxutils.escape(json.dumps(user_info), escapedict),
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
                #                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except User.DoesNotExist:
        raise Http404
