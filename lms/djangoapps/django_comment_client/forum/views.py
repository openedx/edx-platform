from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
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
from django_comment_client.utils import merge_dict, extract, strip_none, strip_blank

import json
import django_comment_client.utils as utils
import comment_client as cc


THREADS_PER_PAGE = 50000
PAGES_NEARBY_DELTA = 2


def _general_discussion_id(course_id):
    return course_id.replace('/', '_').replace('.', '_')

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
        'forum': (lambda: reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id])),
        'user': (lambda: reverse('django_comment_client.forum.views.user_profile', args=[course_id, user_id])),
    }[discussion_type]()

    user_info = cc.User.from_django_user(request.user).to_dict()

    def infogetter(thread):
        return utils.get_annotated_content_infos(course_id, thread, request.user, user_info)

    annotated_content_info = reduce(merge_dict, map(infogetter, threads), {})

    context = {
        'threads': threads,
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

def get_threads(request, course_id, discussion_id=None):

    default_query_params = {
        'page': 1,
        'per_page': THREADS_PER_PAGE,
        'sort_key': 'activity',
        'sort_order': 'desc',
        'text': '',
        'tags': '',
        'commentable_id': discussion_id,
        'course_id': course_id,
    }

    query_params = merge_dict(default_query_params,
                              strip_none(extract(request.GET, ['page', 'sort_key', 'sort_order', 'text', 'tags'])))

    threads, page, num_pages = cc.Thread.search(query_params)

    query_params['page'] = page
    query_params['num_pages'] = num_pages

    return threads, query_params

# discussion per page is fixed for now
def inline_discussion(request, course_id, discussion_id):
    threads, query_params = get_threads(request, course_id, discussion_id)
    html = render_inline_discussion(request, course_id, threads, discussion_id=discussion_id,  \
                                                                 query_params=query_params)
    
    return utils.JsonResponse({
        'html': html,
        'discussion_data': map(utils.safe_content, threads),
    })

def render_search_bar(request, course_id, discussion_id=None, text=''):
    if not discussion_id:
        return ''
    context = {
        'discussion_id': discussion_id,
        'text': text,
        'course_id': course_id,
    }
    return render_to_string('discussion/_search_bar.html', context)

def forum_form_discussion(request, course_id):
    course = get_course_with_access(request.user, course_id, 'load')
    threads, query_params = get_threads(request, course_id)
    content = render_forum_discussion(request, course_id, threads, discussion_id=_general_discussion_id(course_id), query_params=query_params)

    if request.is_ajax():
        return utils.JsonResponse({
            'html': content,
            'discussion_data': map(utils.safe_content, threads),
        })
    else:
        recent_active_threads = cc.search_recent_active_threads(
            course_id,
            recursive=False,
            query_params={'follower_id': request.user.id},
        )

        trending_tags = cc.search_trending_tags(
            course_id,
        )
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'content': content,
            'recent_active_threads': recent_active_threads,
            'trending_tags': trending_tags,
            'staff_access' : has_access(request.user, course, 'staff'),
            'threads': threads,
        }
        # print "start rendering.."
        return render_to_response('discussion/index.html', context)

def render_single_thread(request, discussion_id, course_id, thread_id):
    
    thread = cc.Thread.find(thread_id).retrieve(recursive=True).to_dict()
    threads, query_params = get_threads(request, course_id)

    user_info = cc.User.from_django_user(request.user).to_dict()

    annotated_content_info = utils.get_annotated_content_infos(course_id, thread=thread, user=request.user, user_info=user_info)

    context = {
        'discussion_id': discussion_id,
        'thread': thread,
        'annotated_content_info': json.dumps(annotated_content_info),
        'course_id': course_id,
        'request': request,
        'discussion_data': json.dumps({ discussion_id: [utils.safe_content(thread)] }),
        'threads': threads,
    }

    return render_to_string('discussion/_single_thread.html', context)

def single_thread(request, course_id, discussion_id, thread_id):

    if request.is_ajax():
        
        user_info = cc.User.from_django_user(request.user).to_dict()
        thread = cc.Thread.find(thread_id).retrieve(recursive=True)
        annotated_content_info = utils.get_annotated_content_infos(course_id, thread, request.user, user_info=user_info)
        context = {'thread': thread.to_dict(), 'course_id': course_id}
        html = render_to_string('discussion/_ajax_single_thread.html', context)

        return utils.JsonResponse({
            'html': html,
            'content': utils.safe_content(thread.to_dict()),
            'annotated_content_info': annotated_content_info,
        })

    else:
        course = get_course_with_access(request.user, course_id, 'load')
        threads, query_params = get_threads(request, course_id)

        recent_active_threads = cc.search_recent_active_threads(
            course_id,
            recursive=False,
            query_params={'follower_id': request.user.id},
        )

        trending_tags = cc.search_trending_tags(
            course_id,
        )

        user_info = cc.User.from_django_user(request.user).to_dict()

        context = {
            'discussion_id': discussion_id,
            'csrf': csrf(request)['csrf_token'],
            'init': '',
            'user_info': json.dumps(user_info),
            'content': render_single_thread(request, discussion_id, course_id, thread_id),
            'course': course,
            'recent_active_threads': recent_active_threads,
            'trending_tags': trending_tags,
            'course_id': course.id,
            'thread_id': thread_id,
            'threads': json.dumps(threads),
        }

        return render_to_response('discussion/single_thread.html', context)

def user_profile(request, course_id, user_id):

    course = get_course_with_access(request.user, course_id, 'load')
    profiled_user = cc.User(id=user_id, course_id=course_id)

    query_params = {
        'page': request.GET.get('page', 1),
        'per_page': THREADS_PER_PAGE, # more than threads_per_page to show more activities
    }

    threads, page, num_pages = profiled_user.active_threads(query_params)

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
