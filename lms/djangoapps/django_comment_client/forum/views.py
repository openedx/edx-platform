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
from django.views.decorators.cache import never_cache

THREADS_PER_PAGE = 20
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

def threads_context(user, threads, course_id, page, num_pages):
    """
    Convenience function for DRYing up views that all generate roughly the same data
    """
    user_info = cc.User.from_django_user(user).to_dict()
    annotated_content_info = utils.get_metadata_for_threads(course_id, threads, user, user_info)

    return {
        'threads': [utils.safe_content(thread) for thread in threads],
        'user_info': user_info, # TODO: This should not be returned on each JSON response
        'annotated_content_info': annotated_content_info,
        'page': page,
        'num_pages': num_pages,
        'roles': utils.get_role_ids(course_id), # TODO: This should not be returned on each JSON response
    }

def add_courseware_context(thread, course):
    courseware_context = get_courseware_context(thread, course)
    if courseware_context:
        thread.update(courseware_context)
    return thread

def get_anonymous_permissions(context, course):
    context['allow_anonymous'] = course.metadata.get("allow_anonymous", True)
    context['allow_anonymous_to_peers']= course.metadata.get("allow_anonymous_to_peers", False)
    return context

def inline_discussion(request,
                      course_id, discussion_id):
    """
    Renders JSON for DiscussionModules
    """

    course = get_course_with_access(request.user, course_id, 'load')

    try:
        threads, query_params = get_threads(request, course_id, discussion_id, per_page=THREADS_PER_PAGE)
        context = threads_context(request.user, threads, course_id, query_params['page'], query_params['num_pages'])
        get_anonymous_permissions(context, course)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        # TODO (vshnayder): since none of this code seems to be aware of the fact that
        # sometimes things go wrong, I suspect that the js client is also not
        # checking for errors on request.  Check and fix as needed.
        log.error("Error loading inline discussion threads.")
        raise Http404   #TODO: Send a status code that makes sense

    return utils.JsonResponse(context)

@login_required
@never_cache
def forum_form_discussion(request, course_id):
    """
    Renders the main Discussion page, potentially filtered by a search query
    """
    course = get_course_with_access(request.user, course_id, 'load')
    category_map = utils.get_discussion_category_map(course)

    try:
        unsafethreads, query_params = get_threads(request, course_id)   # This might process a search query
        for thread in unsafethreads:
            add_courseware_context(thread, course)
        context = threads_context(request.user, unsafethreads, course_id, query_params['page'], query_params['num_pages'])
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        log.error("Error loading forum discussion threads: %s" % str(err))
        raise Http404

    if request.is_ajax():
        del context['roles']
        return utils.JsonResponse(context)
    else:
        context.update({
            'course': course,
            'staff_access' : has_access(request.user, course, 'staff'),
            'category_map': category_map,
        })
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
        annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, user_info=user_info)
        content = utils.safe_content(thread.to_dict())
        add_courseware_context(content, course)
        return utils.JsonResponse({
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
            add_courseware_context(thread, course)

        context = threads_context(request.user, threads, course_id, query_params['page'], query_params['num_pages'])
        context.update({
            'discussion_id': discussion_id,
            'course': course,
            'thread_id': thread_id,
            'category_map': category_map,
        })

        return render_to_response('discussion/single_thread.html', context)

@login_required
def user_profile(request, course_id, user_id):
    #TODO: Allow sorting?
    course = get_course_with_access(request.user, course_id, 'load')
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE,
            }

        threads, page, num_pages = profiled_user.active_threads(query_params)
        context = threads_context(request.user, threads, course_id, page, num_pages)

        if request.is_ajax():
            del context['roles']
            return utils.JsonResponse(context)
        else:
            context.update({
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
            })

            return render_to_response('discussion/user_profile.html', context)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404

def followed_threads(request, course_id, user_id):
    course = get_course_with_access(request.user, course_id, 'load')
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params = {
            'page': request.GET.get('page', 1),
            'per_page': THREADS_PER_PAGE,
            'sort_key': request.GET.get('sort_key', 'date'),
            'sort_order': request.GET.get('sort_order', 'desc'),
        }

        threads, page, num_pages = profiled_user.subscribed_threads(query_params)
        context = threads_context(request.user, threads, course_id, page, num_pages)
        del context['roles']
        return utils.JsonResponse(context)

    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404
