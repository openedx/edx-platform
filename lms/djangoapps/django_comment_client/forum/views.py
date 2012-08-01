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

from django_comment_client.utils import get_categorized_discussion_info
from urllib import urlencode

import json
import comment_client
import dateutil


THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2

class HtmlResponse(HttpResponse):
    def __init__(self, html=''):
        super(HtmlResponse, self).__init__(html, content_type='text/plain')

def render_accordion(request, course, discussion_id):

    discussion_info = get_categorized_discussion_info(request, course)

    context = {
        'course': course,
        'discussion_info': discussion_info,
        'active': discussion_id,
        'csrf': csrf(request)['csrf_token'],
    }

    return render_to_string('discussion/_accordion.html', context)

def render_discussion(request, course_id, threads, discussion_id=None, with_search_bar=True, 
                      search_text='', discussion_type='inline', page=1, num_pages=None, 
                      per_page=THREADS_PER_PAGE, url_for_page=None):
    template = {
        'inline': 'discussion/_inline.html',
        'forum': 'discussion/_forum.html',
    }[discussion_type]

    def _url_for_inline_page(page, per_page):
        raw_url = reverse('django_comment_client.forum.views.inline_discussion', args=[course_id, discussion_id])
        return raw_url + '?' + urlencode({'page': page, 'per_page': per_page})

    def _url_for_forum_page(page, per_page):
        raw_url = reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id, discussion_id])
        return raw_url + '?' + urlencode({'page': page, 'per_page': per_page})

    url_for_page = {
        'inline': _url_for_inline_page,
        'forum': _url_for_forum_page,
    }[discussion_type]

    
    context = {
        'threads': threads,
        'discussion_id': discussion_id,
        'search_bar': '' if not with_search_bar \
                      else render_search_bar(request, course_id, discussion_id, text=search_text),
        'user_info': comment_client.get_user_info(request.user.id, raw=True),
        'course_id': course_id,
        'request': request,
        'page': page,
        'per_page': per_page,
        'num_pages': num_pages,
        'pages_nearby_delta': PAGES_NEARBY_DELTA,
        'discussion_type': discussion_type,
        'url_for_page': url_for_page,
    }
    return render_to_string(template, context)

def render_inline_discussion(*args, **kwargs):
    
    return render_discussion(discussion_type='inline', *args, **kwargs)

def render_forum_discussion(*args, **kwargs):
    return render_discussion(discussion_type='forum', *args, **kwargs)

# discussion per page is fixed for now
def inline_discussion(request, course_id, discussion_id):
    formpage = request.GET.get('page', 1)
    threads, page, num_pages = comment_client.get_threads(discussion_id, recursive=False, page=page, per_page=THREADS_PER_PAGE)
    html = render_inline_discussion(request, course_id, threads, discussion_id=discussion_id, num_pages=num_pages, page=page)
    return HtmlResponse(html)

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
    search_text = request.GET.get('text', '')
    page = request.GET.get('page', 1)

    if len(search_text) > 0:
        threads, page, per_page, num_pages = comment_client.search_threads({
            'text': search_text,
            'commentable_id': discussion_id,
            'course_id': course_id,
            'page': page,
            'per_page': THREADS_PER_PAGE,
        })
    else:
        threads, page, per_page, num_pages = comment_client.get_threads(discussion_id, recursive=False, page=page, per_page=THREADS_PER_PAGE)

    context = {
        'csrf': csrf(request)['csrf_token'],
        'course': course,
        'content': render_forum_discussion(request, course_id, threads, 
                                           discussion_id=discussion_id,
                                           search_text=search_text,
                                           num_pages=num_pages,
                                           per_page=per_page,
                                           page=page),
        'accordion': render_accordion(request, course, discussion_id),
    }

    return render_to_response('discussion/index.html', context)

def render_single_thread(request, course_id, thread_id):
    
    def get_annotated_content_info(thread, user_id):
        infos = {}
        def _annotate(content):
            infos[str(content['id'])] = {
                'editable': str(content['user_id']) == str(user_id), # TODO may relax this to instructors
            }
            for child in content['children']:
                _annotate(child)
        _annotate(thread)
        return infos

    thread = comment_client.get_thread(thread_id, recursive=True)

    context = {
        'thread': thread,
        'user_info': comment_client.get_user_info(request.user.id, raw=True),
        'annotated_content_info': json.dumps(get_annotated_content_info(thread=thread, user_id=request.user.id)),
        'course_id': course_id,
        'request': request,
    }
    return render_to_string('discussion/_single_thread.html', context)

def single_thread(request, course_id, discussion_id, thread_id):

    course = check_course(course_id)

    context = {
        'csrf': csrf(request)['csrf_token'],
        'init': '',
        'content': render_single_thread(request, course_id, thread_id),
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
