from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import simplejson
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from mitxmako.shortcuts import render_to_response, render_to_string
from courseware.courses import get_course_with_access

from dateutil.tz import tzlocal
from datehelper import time_ago_in_words

import django_comment_client.utils as utils
from urllib import urlencode

import json
import comment_client as cc
import dateutil


THREADS_PER_PAGE = 5
PAGES_NEARBY_DELTA = 2

def _should_perform_search(request):
    return bool(request.GET.get('text', False) or \
            request.GET.get('tags', False))
        

def render_accordion(request, course, discussion_id):

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
        'forum': (lambda: reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id, discussion_id])),
        'user': (lambda: reverse('django_comment_client.forum.views.user_profile', args=[course_id, user_id])),
    }[discussion_type]()

    print "start annotating"
    annotated_content_infos = map(lambda x: utils.get_annotated_content_infos(course_id, x, request.user, type='thread'), threads)
    print "start merging annotations"
    annotated_content_info = reduce(utils.merge_dict, annotated_content_infos, {})
    print "finished annotating"

    context = {
        'threads': threads,
        'discussion_id': discussion_id,
        'user_id': user_id,
        'user_info': json.dumps(cc.User.from_django_user(request.user).to_dict()),
        'course_id': course_id,
        'request': request,
        'performed_search': _should_perform_search(request),
        'pages_nearby_delta': PAGES_NEARBY_DELTA,
        'discussion_type': discussion_type,
        'base_url': base_url,
        'query_params': utils.strip_none(utils.extract(query_params, ['page', 'sort_key', 'sort_order', 'tags', 'text'])),
        'annotated_content_info': json.dumps(annotated_content_info),
    }
    context = dict(context.items() + query_params.items())
    return render_to_string(template, context)

def render_inline_discussion(*args, **kwargs):
    return render_discussion(discussion_type='inline', *args, **kwargs)

def render_forum_discussion(*args, **kwargs):
    return render_discussion(discussion_type='forum', *args, **kwargs)

def render_user_discussion(*args, **kwargs):
    return render_discussion(discussion_type='user', *args, **kwargs)

def get_threads(request, course_id, discussion_id):
    query_params = {
        'page': request.GET.get('page', 1),
        'per_page': THREADS_PER_PAGE, #TODO maybe change this later
        'sort_key': request.GET.get('sort_key', 'date'),
        'sort_order': request.GET.get('sort_order', 'desc'),
        'text': request.GET.get('text', ''), 
        'tags': request.GET.get('tags', ''),
        'commentable_id': discussion_id,
        'course_id': course_id,
    }

    threads, page, num_pages = cc.Thread.search(query_params)

    query_params['page'] = page
    query_params['num_pages'] = num_pages

    return threads, query_params

# discussion per page is fixed for now
def inline_discussion(request, course_id, discussion_id):
    threads, query_params = get_threads(request, course_id, discussion_id)
    html = render_inline_discussion(request, course_id, threads, discussion_id=discussion_id,  \
                                                                 query_params=query_params)
    return utils.HtmlResponse(html)

def render_search_bar(request, course_id, discussion_id=None, text=''):
    if not discussion_id:
        return ''
    context = {
        'discussion_id': discussion_id,
        'text': text,
        'course_id': course_id,
    }
    return render_to_string('discussion/_search_bar.html', context)

def forum_form_discussion(request, course_id, discussion_id):
    course = get_course_with_access(request.user, course_id, 'load')
    threads, query_params = get_threads(request, course_id, discussion_id)
    content = render_forum_discussion(request, course_id, threads, discussion_id=discussion_id, \
                                                                   query_params=query_params)

    recent_active_threads = cc.search_recent_active_threads(
        course_id,
        recursive=False,
        query_params={'follower_id': request.user.id,
                      'commentable_id': discussion_id},
    )

    trending_tags = cc.search_trending_tags(
        course_id,
        query_params={'commentable_id': discussion_id},
    )

    if request.is_ajax():
        return utils.HtmlResponse(content)
    else:
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'content': content,
            'accordion': render_accordion(request, course, discussion_id),
            'recent_active_threads': recent_active_threads,
            'trending_tags': trending_tags,
        }
        return render_to_response('discussion/index.html', context)

def render_single_thread(request, discussion_id, course_id, thread_id):
    
    thread = cc.Thread.find(thread_id).retrieve(recursive=True)

    annotated_content_info = utils.get_annotated_content_infos(course_id, thread=thread.to_dict(), \
                                                               user=request.user, type='thread')

    context = {
        'discussion_id': discussion_id,
        'thread': thread,
        'user_info': json.dumps(cc.User.from_django_user(request.user).to_dict()),
        'annotated_content_info': json.dumps(annotated_content_info),
        'course_id': course_id,
        'request': request,
    }
    return render_to_string('discussion/_single_thread.html', context)

def single_thread(request, course_id, discussion_id, thread_id):

    if request.is_ajax():
        
        thread = cc.Thread.find(thread_id).retrieve(recursive=True)
        annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, type='thread')
        context = {'thread': thread.to_dict(), 'course_id': course_id}
        html = render_to_string('discussion/_ajax_single_thread.html', context)

        return utils.JsonResponse({
            'html': html,
            'annotated_content_info': annotated_content_info,
        })

    else:
        course = get_course_with_access(request.user, course_id, 'load')

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',
            'content': render_single_thread(request, discussion_id, course_id, thread_id),
            'accordion': render_accordion(request, course, discussion_id),
            'course': course,
            'course_id': course.id,
        }

        return render_to_response('discussion/index.html', context)

def user_profile(request, course_id, user_id):

    course = get_course_with_access(request.user, course_id, 'load')
    discussion_user = cc.User(id=user_id, course_id=course_id)

    query_params = {
        'page': request.GET.get('page', 1),
        'per_page': THREADS_PER_PAGE, # more than threads_per_page to show more activities
    }

    threads, page, num_pages = discussion_user.active_threads(query_params)

    query_params['page'] = page
    query_params['num_pages'] = num_pages

    content = render_user_discussion(request, course_id, threads, user_id=user_id, query_params=query_params)

    if request.is_ajax():
        return utils.HtmlResponse(content)
    else:
        context = {
            'course': course, 
            'user': request.user,
            'django_user': User.objects.get(id=user_id),
            'discussion_user': discussion_user.to_dict(),
            'content': content,
        }

        return render_to_response('discussion/user_profile.html', context)
