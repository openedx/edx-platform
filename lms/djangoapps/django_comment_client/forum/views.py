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

THREADS_PER_PAGE = 200
INLINE_THREADS_PER_PAGE = 5
PAGES_NEARBY_DELTA = 2

log = logging.getLogger("edx.discussions")

def _general_discussion_id(course_id):
    return course_id.replace('/', '_').replace('.', '_')

def _should_perform_search(request):
    return bool(request.GET.get('text', False) or \
            request.GET.get('tags', False))

def render_accordion(request, course, discussion_id):
    # TODO: Delete if obsolete
    discussion_info = utils.get_categorized_discussion_info(request, course)

    context = {
        'course': course,
        'discussion_info': discussion_info,
        'active': discussion_id,
        'csrf': csrf(request)['csrf_token'],
    }

    return render_to_string('discussion/_accordion.html', context)

def render_discussion(request, course_id, threads, *args, **kwargs):

    discussion_id = kwargs.get('discussion_id')
    user_id = kwargs.get('user_id')
    discussion_type = kwargs.get('discussion_type', 'inline')
    query_params = kwargs.get('query_params', {})

    template = {
        'inline': 'discussion/_inline.html',
        'forum': 'discussion/_forum.html',
        'user': 'discussion/_user_active_threads.html',
    }[discussion_type]

    base_url = {
        'inline': (lambda: reverse('django_comment_client.forum.views.inline_discussion', args=[course_id, discussion_id])),
        'forum': (lambda: reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id])),
        'user': (lambda: reverse('django_comment_client.forum.views.user_profile', args=[course_id, user_id])),
    }[discussion_type]()

    user_info = cc.User.from_django_user(request.user).to_dict()

    def infogetter(thread):
        return utils.get_annotated_content_infos(course_id, thread, request.user, user_info)

    annotated_content_info = reduce(merge_dict, map(infogetter, threads), {})

    if discussion_type != 'inline':
        course = get_course_with_access(request.user, course_id, 'load')

        for thread in threads:
            courseware_context = get_courseware_context(thread, course)
            if courseware_context:
                thread['courseware_location']  = courseware_context['courseware_location']
                thread['courseware_title']  = courseware_context['courseware_title']

    context = {
        #'threads': map(utils.safe_content, threads),   # TODO Delete, this is redundant with discussion_data
        'discussion_id': discussion_id,
        'user_id': user_id,
        'course_id': course_id,
        'request': request,
        'performed_search': _should_perform_search(request),
        'pages_nearby_delta': PAGES_NEARBY_DELTA,
        'discussion_type': discussion_type,
        'base_url': base_url,
        'query_params': strip_blank(strip_none(extract(query_params, ['page', 'sort_key', 'sort_order', 'tags', 'text']))),
        'annotated_content_info': json.dumps(annotated_content_info),
        'discussion_data': json.dumps({ (discussion_id or user_id): map(utils.safe_content, threads) })
    }
    context = dict(context.items() + query_params.items())
    return render_to_string(template, context)

def render_inline_discussion(*args, **kwargs):
    return render_discussion(discussion_type='inline', *args, **kwargs)

def render_forum_discussion(*args, **kwargs):
    return render_discussion(discussion_type='forum', *args, **kwargs)

def render_user_discussion(*args, **kwargs):
    return render_discussion(discussion_type='user', *args, **kwargs)

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
                              strip_none(extract(request.GET, ['page', 'sort_key', 'sort_order', 'text', 'tags'])))

    threads, page, num_pages = cc.Thread.search(query_params)

    query_params['page'] = page
    query_params['num_pages'] = num_pages

    return threads, query_params

def inline_discussion(request, course_id, discussion_id):
    """
    Renders JSON for DiscussionModules
    """

    try:
        threads, query_params = get_threads(request, course_id, discussion_id, per_page=INLINE_THREADS_PER_PAGE)
        user_info = cc.User.from_django_user(request.user).to_dict()
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        # TODO (vshnayder): since none of this code seems to be aware of the fact that
        # sometimes things go wrong, I suspect that the js client is also not
        # checking for errors on request.  Check and fix as needed.
        raise Http404

    # TODO: Remove all of this stuff or switch back to server side rendering once templates are mustache again
    #html = render_inline_discussion(request, course_id, threads, discussion_id=discussion_id,  \
    #                                                             query_params=query_params)

    def infogetter(thread):
        return utils.get_annotated_content_infos(course_id, thread, request.user, user_info)

    annotated_content_info = reduce(merge_dict, map(infogetter, threads), {})

    return utils.JsonResponse({
#        'html': html,
        'discussion_data': map(utils.safe_content, threads),
        'user_info': user_info,
        'annotated_content_info': annotated_content_info,
        'page': query_params['page'],
        'num_pages': query_params['num_pages']
    })

def forum_form_discussion(request, course_id):
    """
    Renders the main Discussion page
    """
    course = get_course_with_access(request.user, course_id, 'load')
    category_map = utils.get_discussion_category_map(course)

    try:
        unsafethreads, query_params = get_threads(request, course_id)
        threads = [utils.safe_content(thread) for thread in unsafethreads]
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404

    #content = render_forum_discussion(request, course_id, threads, discussion_id=_general_discussion_id(course_id), query_params=query_params)

    user_info = cc.User.from_django_user(request.user).to_dict()

    def infogetter(thread):
        return utils.get_annotated_content_infos(course_id, thread, request.user, user_info)

    annotated_content_info = reduce(merge_dict, map(infogetter, threads), {})

    if request.is_ajax():
        return utils.JsonResponse({
            #'html': content,
            'discussion_data': threads,
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
        escapedict = {'"': '&quot;'}
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            #'content': content,
            #'recent_active_threads': recent_active_threads,
            #'trending_tags': trending_tags,
            'staff_access' : has_access(request.user, course, 'staff'),
            'threads': saxutils.escape(json.dumps(threads),escapedict),
            'user_info': saxutils.escape(json.dumps(user_info),escapedict),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info),escapedict),
            'course_id': course.id,
            'category_map': category_map,
        }
        # print "start rendering.."
        return render_to_response('discussion/index.html', context)

def single_thread(request, course_id, discussion_id, thread_id):

    if request.is_ajax():
        course = get_course_with_access(request.user, course_id, 'load')
        user_info = cc.User.from_django_user(request.user).to_dict()

        try:
            thread = cc.Thread.find(thread_id).retrieve(recursive=True)
        except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
            raise Http404
        courseware_context = get_courseware_context(thread, course)

        annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, user_info=user_info)
        context = {'thread': thread.to_dict(), 'course_id': course_id}
        # TODO: Remove completely or switch back to server side rendering
        html = render_to_string('discussion/_ajax_single_thread.html', context)
        content = utils.safe_content(thread.to_dict())
        if courseware_context:
            content.update(courseware_context)
        return utils.JsonResponse({
            'html': html,
            'content': content,
            'annotated_content_info': annotated_content_info,
        })

    else:
        course = get_course_with_access(request.user, course_id, 'load')
        category_map = utils.get_discussion_category_map(course)
        try:
            threads, query_params = get_threads(request, course_id)
        except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
            raise Http404

        course = get_course_with_access(request.user, course_id, 'load')

        for thread in threads:
            courseware_context = get_courseware_context(thread, course)
            if courseware_context:
                thread['courseware_location']  = courseware_context['courseware_location']
                thread['courseware_title']  = courseware_context['courseware_title']

        #recent_active_threads = cc.search_recent_active_threads(
        #    course_id,
        #    recursive=False,
        #    query_params={'follower_id': request.user.id},
        #)

        #trending_tags = cc.search_trending_tags(
        #    course_id,
        #)

        user_info = cc.User.from_django_user(request.user).to_dict()
        escapedict = {'"': '&quot;'}

        def infogetter(thread):
            return utils.get_annotated_content_infos(course_id, thread, request.user, user_info)

        annotated_content_info = reduce(merge_dict, map(infogetter, threads), {})

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',
            'user_info': saxutils.escape(json.dumps(user_info),escapedict),
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            'course': course,
            #'recent_active_threads': recent_active_threads,
            #'trending_tags': trending_tags,
            'course_id': course.id,
            'thread_id': thread_id,
            'threads': saxutils.escape(json.dumps(threads), escapedict),
            'category_map': category_map,
        }

        return render_to_response('discussion/single_thread.html', context)

def user_profile(request, course_id, user_id):

    course = get_course_with_access(request.user, course_id, 'load')
    try:
        profiled_user = cc.User(id=user_id, course_id=course_id)

        query_params['page'] = page
        query_params['num_pages'] = num_pages

        content = render_user_discussion(request, course_id, threads, user_id=user_id, query_params=query_params)

        if request.is_ajax():
            return utils.JsonResponse({
                'html': content,
                'discussion_data': map(utils.safe_content, threads),
            })
        else:
            context = {
                'course': course,
                'user': request.user,
                'django_user': User.objects.get(id=user_id),
                'profiled_user': profiled_user.to_dict(),
                'content': content,
            }

            return render_to_response('discussion/user_profile.html', context)
    except (cc.utils.CommentClientError, cc.utils.CommentClientUnknownError) as err:
        raise Http404
