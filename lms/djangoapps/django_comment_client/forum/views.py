from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import simplejson
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

from mitxmako.shortcuts import render_to_response, render_to_string
from courseware.courses import check_course

from dateutil.tz import tzlocal
from datehelper import time_ago_in_words

import django_comment_client.utils as utils
from urllib import urlencode

import json
import comment_client
import dateutil

from django_comment_client.permissions import check_permissions_by_view

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

def render_discussion(request, course_id, threads, discussion_id=None, \
                      discussion_type='inline', query_params={}):

    template = {
        'inline': 'discussion/_inline.html',
        'forum': 'discussion/_forum.html',
    }[discussion_type]

    base_url = {
        'inline': (lambda: reverse('django_comment_client.forum.views.inline_discussion', args=[course_id, discussion_id])), 
        'forum': (lambda: reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id, discussion_id])),
    }[discussion_type]()

    annotated_content_info = {thread['id']: get_annotated_content_info(course_id, thread, request.user, is_thread=True) for thread in threads}

    context = {
        'threads': threads,
        'discussion_id': discussion_id,
        'user_info': comment_client.get_user_info(request.user.id, raw=True),
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

def get_threads(request, course_id, discussion_id):
    query_params = {
        'page': request.GET.get('page', 1),
        'per_page': THREADS_PER_PAGE, #TODO maybe change this later
        'sort_key': request.GET.get('sort_key', 'date'),
        'sort_order': request.GET.get('sort_order', 'desc'),
        'text': request.GET.get('text', ''), 
        'tags': request.GET.get('tags', ''),
    }

    if _should_perform_search(request):
        query_params['commentable_id'] = discussion_id
        threads, page, num_pages = comment_client.search_threads(course_id, recursive=False, query_params=utils.strip_none(query_params))
    else:
        threads, page, num_pages = comment_client.get_threads(discussion_id, recursive=False, query_params=utils.strip_none(query_params))

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
    course = check_course(course_id)
    threads, query_params = get_threads(request, course_id, discussion_id)
    content = render_forum_discussion(request, course_id, threads, discussion_id=discussion_id, \
                                                                   query_params=query_params)

    if request.is_ajax():
        return utils.HtmlResponse(content)
    else:
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'content': content,
            'accordion': render_accordion(request, course, discussion_id),
        }
        return render_to_response('discussion/index.html', context)


def get_annotated_content_info(course_id, content, user, is_thread):
    return {
        'editable': check_permissions_by_view(user, course_id, content, "update_thread" if is_thread else "update_comment"),
        'can_reply': check_permissions_by_view(user, course_id, content, "create_comment" if is_thread else "create_sub_comment"),
        'can_endorse': check_permissions_by_view(user, course_id, content, "endorse_comment") if not is_thread else False,
        'can_delete': check_permissions_by_view(user, course_id, content, "delete_thread" if is_thread else "delete_comment"),
    }

def get_annotated_content_infos(course_id, thread, user, is_thread=True):
    infos = {}
    def _annotate(content, is_thread=is_thread):
        infos[str(content['id'])] = get_annotated_content_info(course_id, content, user, is_thread)
        for child in content.get('children', []):
            _annotate(child, is_thread=False)
    _annotate(thread)
    return infos

def render_single_thread(request, discussion_id, course_id, thread_id):
    
    thread = comment_client.get_thread(thread_id, recursive=True)

    annotated_content_info = get_annotated_content_infos(course_id, thread=thread, \
                                user=request.user, is_thread=True)

    context = {
        'discussion_id': discussion_id,
        'thread': thread,
        'user_info': comment_client.get_user_info(request.user.id, raw=True),
        'annotated_content_info': json.dumps(annotated_content_info),
        'course_id': course_id,
        'request': request,
    }
    return render_to_string('discussion/_single_thread.html', context)

def single_thread(request, course_id, discussion_id, thread_id):

    if request.is_ajax():
        
        thread = comment_client.get_thread(thread_id, recursive=True)
        annotated_content_info = get_annotated_content_infos(course_id, thread, request.user)
        context = {'thread': thread}
        html = render_to_string('discussion/_ajax_single_thread.html', context)

        return utils.JsonResponse({
            'html': html,
            'annotated_content_info': annotated_content_info,
        })

    else:
        course = check_course(course_id)

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',
            'content': render_single_thread(request, discussion_id, course_id, thread_id),
            'accordion': render_accordion(request, course, discussion_id),
            'course': course,
        }

        return render_to_response('discussion/index.html', context)

def search(request, course_id):

    course = check_course(course_id)

    text = request.GET.get('text', None)
    commentable_id = request.GET.get('commentable_id', None)
    tags = request.GET.get('tags', None)

    threads = comment_client.search_threads({
        'text': text,
        'commentable_id': commentable_id,
        'tags': tags,
    })

    context = {
        'csrf': csrf(request)['csrf_token'],
        'init': '',
        'content': render_forum_discussion(request, course_id, threads, search_text=text),
        'accordion': '',
        'course': course,
    }

    return render_to_response('discussion/index.html', context)
