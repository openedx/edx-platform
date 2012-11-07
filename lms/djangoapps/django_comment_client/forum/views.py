import json
import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from mitxmako.shortcuts import render_to_response, render_to_string
from courseware.courses import get_course_with_access
from courseware.access import has_access

from urllib import urlencode
from operator import methodcaller
from django_comment_client.permissions import check_permissions_by_view
from django_comment_client.utils import merge_dict, extract, strip_none, strip_blank, get_courseware_context

import django_comment_client.utils as utils
import comment_client as cc
import xml.sax.saxutils as saxutils

THREADS_PER_PAGE = 20
INLINE_THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2
escapedict = {'"': '&quot;'}
log = logging.getLogger("edx.discussions")

def get_threads(request, course_id, discussion_id=None, per_page=THREADS_PER_PAGE):
    """
    This may raise cc.utils.CommentClientError or
    cc.utils.CommentClientUnknownError if something goes wrong.
    """

    default_query_params = {
        'page': 1,
        'per_page': per_page,
        'sort_key': 'date',
        'sort_order': 'desc',
        'text': '',
        'tags': '',
        'commentable_id': discussion_id,
        'course_id': course_id,
        'user_id': request.user.id,
    }

    if not request.GET.get('sort_key'):
        # If the user did not select a sort key, use their last used sort key
        user = cc.User.from_django_user(request.user)
        user.retrieve()
        # TODO: After the comment service is updated this can just be user.default_sort_key because the service returns the default value
        default_query_params['sort_key'] = user.get('default_sort_key') or default_query_params['sort_key']
    else:
        # If the user clicked a sort key, update their default sort key
        user = cc.User.from_django_user(request.user)
        user.default_sort_key = request.GET.get('sort_key')
        user.save()

    query_params = merge_dict(default_query_params,
                              strip_none(extract(request.GET, ['page', 'sort_key', 'sort_order', 'text', 'tags', 'commentable_ids'])))

    threads, page, num_pages = cc.Thread.search(query_params)

    query_params['page'] = page
    query_params['num_pages'] = num_pages

    return threads, query_params

def inline_discussion(request, course_id, discussion_id):
    """
    Renders JSON for DiscussionModules
    """

    course = get_course_with_access(request.user, course_id, 'load')

    try:
        threads, query_params = get_threads(request, course_id, discussion_id, per_page=INLINE_THREADS_PER_PAGE)
        user_info = cc.User.from_django_user(request.user).to_dict()
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        # TODO (vshnayder): since none of this code seems to be aware of the fact that
        # sometimes things go wrong, I suspect that the js client is also not
        # checking for errors on request.  Check and fix as needed.
        log.error("Error loading inline discussion threads.")
        raise Http404

    annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

    allow_anonymous = course.metadata.get("allow_anonymous", True)
    allow_anonymous_to_peers = course.metadata.get("allow_anonymous_to_peers", False)

    return utils.JsonResponse({
        'discussion_data': map(utils.safe_content, threads),
        'user_info': user_info,
        'annotated_content_info': annotated_content_info,
        'page': query_params['page'],
        'num_pages': query_params['num_pages'],
        'roles': utils.get_role_ids(course_id),
        'allow_anonymous_to_peers': allow_anonymous_to_peers,
        'allow_anonymous': allow_anonymous,
    })

@login_required
def forum_form_discussion(request, course_id):
    """
    Renders the main Discussion page, potentially filtered by a search query
    """
    course = get_course_with_access(request.user, course_id, 'load')
    category_map = utils.get_discussion_category_map(course)

    try:
        unsafethreads, query_params = get_threads(request, course_id)   # This might process a search query
        threads = [utils.safe_content(thread) for thread in unsafethreads]
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        log.error("Error loading forum discussion threads: %s" % str(err))
        raise Http404

    user_info = cc.User.from_django_user(request.user).to_dict()

    annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

    for thread in threads:
        courseware_context = get_courseware_context(thread, course)
        if courseware_context:
            thread.update(courseware_context)
    if request.is_ajax():
        return utils.JsonResponse({
            'discussion_data': threads, # TODO: Standardize on 'discussion_data' vs 'threads'
            'annotated_content_info': annotated_content_info,
            'num_pages': query_params['num_pages'],
            'page': query_params['page'],
        })
    else:
        #recent_active_threads = cc.search_recent_active_threads(
        #    course_id,
        #    recursive=False,
        #    query_params={'follower_id': request.user.id},
        #)

        #trending_tags = cc.search_trending_tags(
        #    course_id,
        #)

        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            #'recent_active_threads': recent_active_threads,
            #'trending_tags': trending_tags,
            'staff_access' : has_access(request.user, course, 'staff'),
            'threads': saxutils.escape(json.dumps(threads),escapedict),
            'thread_pages': query_params['num_pages'],
            'user_info': saxutils.escape(json.dumps(user_info),escapedict),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info),escapedict),
            'course_id': course.id,
            'category_map': category_map,
            'roles': saxutils.escape(json.dumps(utils.get_role_ids(course_id)), escapedict),
        }
        # print "start rendering.."
        return render_to_response('discussion/index.html', context)

@login_required
def single_thread(request, course_id, discussion_id, thread_id):

    course = get_course_with_access(request.user, course_id, 'load')
    cc_user = cc.User.from_django_user(request.user)
    user_info = cc_user.to_dict()

    try:
        thread = cc.Thread.find(thread_id).retrieve(recursive=True, user_id=request.user.id)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        log.error("Error loading single thread.")
        raise Http404

    if request.is_ajax():

        courseware_context = get_courseware_context(thread, course)

        annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, user_info=user_info)
        context = {'thread': thread.to_dict(), 'course_id': course_id}
        # TODO: Remove completely or switch back to server side rendering
        # html = render_to_string('discussion/_ajax_single_thread.html', context)
        content = utils.safe_content(thread.to_dict())
        if courseware_context:
            content.update(courseware_context)
        return utils.JsonResponse({
            #'html': html,
            'content': content,
            'annotated_content_info': annotated_content_info,
        })

    else:
        category_map = utils.get_discussion_category_map(course)

        try:
            threads, query_params = get_threads(request, course_id)
            threads.append(thread.to_dict())
        except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
            log.error("Error loading single thread.")
            raise Http404

        course = get_course_with_access(request.user, course_id, 'load')

        for thread in threads:
            courseware_context = get_courseware_context(thread, course)
            if courseware_context:
                thread.update(courseware_context)

        threads = [utils.safe_content(thread) for thread in threads]

        #recent_active_threads = cc.search_recent_active_threads(
        #    course_id,
        #    recursive=False,
        #    query_params={'follower_id': request.user.id},
        #)

        #trending_tags = cc.search_trending_tags(
        #    course_id,
        #)

        
        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '', #TODO: What is this?
            'user_info': saxutils.escape(json.dumps(user_info),escapedict),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            'course': course,
            #'recent_active_threads': recent_active_threads,
            #'trending_tags': trending_tags,
            'course_id': course.id, #TODO: Why pass both course and course.id to template?
            'thread_id': thread_id,
            'threads': saxutils.escape(json.dumps(threads), escapedict),
            'category_map': category_map,
            'roles': saxutils.escape(json.dumps(utils.get_role_ids(course_id)), escapedict),
            'thread_pages': query_params['num_pages'],
        }

        return render_to_response('discussion/single_thread.html', context)

@login_required
def user_profile(request, course_id, user_id):
    #TODO: Allow sorting?
    course = get_course_with_access(request.user, course_id, 'load')
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE, # more than threads_per_page to show more activities
            }

        threads, page, num_pages = profiled_user.active_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, request.user, user_info)

        if request.is_ajax():
            return utils.JsonResponse({
                'discussion_data': map(utils.safe_content, threads),
                'page': query_params['page'],
                'num_pages': query_params['num_pages'],
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info),escapedict),
            })
        else:


            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'threads': saxutils.escape(json.dumps(threads), escapedict),
                'user_info': saxutils.escape(json.dumps(user_info),escapedict),
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info),escapedict),
#                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404


def followed_threads(request, course_id, user_id):
    course = get_course_with_access(request.user, course_id, 'load')
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE, # more than threads_per_page to show more activities
            'sort_key': request.GET.get('sort_key', 'date'),
            'sort_order': request.GET.get('sort_order', 'desc'),
        }

        threads, page, num_pages = profiled_user.subscribed_threads(query_params)
        query_params['page'] = page
        query_params['num_pages'] = num_pages
        user_info = cc.User.from_django_user(request.user).to_dict()

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
                'user_info': saxutils.escape(json.dumps(user_info),escapedict),
                'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info),escapedict),
                #                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404
