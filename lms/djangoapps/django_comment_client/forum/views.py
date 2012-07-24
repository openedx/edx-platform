from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.utils import simplejson
from django.core.context_processors import csrf

from mitxmako.shortcuts import render_to_response, render_to_string
from courseware.courses import check_course
from courseware.models import StudentModuleCache
from courseware.module_render import get_module, get_section
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore

from importlib import import_module

from django.conf import settings

import comment_client
import dateutil
from dateutil.tz import tzlocal
from datehelper import time_ago_in_words

import operator
import itertools
import json

_FULLMODULES = None
_DISCUSSIONINFO = None

def get_full_modules():
    global _FULLMODULES
    if not _FULLMODULES:
        class_path = settings.MODULESTORE['default']['ENGINE']
        module_path, _, class_name = class_path.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        modulestore = class_(eager=True, **settings.MODULESTORE['default']['OPTIONS'])
        _FULLMODULES = modulestore.modules
    return _FULLMODULES

def get_categorized_discussion_info(request, user, course, course_name, url_course_id):
    """
        return a dict of the form {category: modules}
    """
    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO:

        _is_course_discussion = lambda x: x[0].dict()['category'] == 'discussion' \
                             and x[0].dict()['course'] == course_name
        
        _get_module_descriptor = operator.itemgetter(1)

        def _get_module(module_descriptor):
            print module_descriptor
            module = get_module(user, request, module_descriptor.location, student_module_cache)[0]
            return module

        def _extract_info(module):
            return {
                'title': module.title,
                'discussion_id': module.discussion_id,
                'category': module.category,
            }

        discussion_module_descriptors = map(_get_module_descriptor,
                                            filter(_is_course_discussion,
                                                   get_full_modules().items()))

        student_module_cache = StudentModuleCache(user, course)

        discussion_info = map(_extract_info, map(_get_module, discussion_module_descriptors))

        _DISCUSSIONINFO = dict((category, list(l)) \
                    for category, l in itertools.groupby(discussion_info, operator.itemgetter('category')))

        _DISCUSSIONINFO['General'] = [{
            'title': 'General discussion',
            'discussion_id': url_course_id,
            'category': 'General',
        }]

    return _DISCUSSIONINFO

def render_accordion(request, course, discussion_info, discussion_id):
    context = {
        'course': course,
        'discussion_info': discussion_info,
        'active': discussion_id,
        'csrf': csrf(request)['csrf_token'],
    }

    return render_to_string('discussion/accordion.html', context)

def render_discussion(request, threads, discussion_id=None, search_text=''):
    context = {
        'threads': threads,
        'discussion_id': discussion_id,
        'search_bar': render_search_bar(request, discussion_id, text=search_text),
    }
    return render_to_string('discussion/inline.html', context)

def render_search_bar(request, discussion_id=None, text=''):
    if not discussion_id:
        return ''
    context = {
        'discussion_id': discussion_id,
        'text': text,
    }
    return render_to_string('discussion/search_bar.html', context)

def forum_form_discussion(request, course_id, discussion_id):

    course_id = course_id.replace('-', '/')
    course = check_course(course_id)

    _, course_name, _ = course_id.split('/')

    url_course_id = course_id.replace('/', '_').replace('.', '_')

    discussion_info = get_categorized_discussion_info(request, request.user, course, course_name, url_course_id)

    search_text = request.GET.get('text', '')

    if len(search_text) > 0:
        threads = comment_client.search(search_text, discussion_id)
    else:
        threads = comment_client.get_threads(discussion_id, recursive=False)

    context = {
        'csrf': csrf(request)['csrf_token'],
        'COURSE_TITLE': course.title,
        'course': course,
        'init': '',
        'content': render_discussion(request, threads, discussion_id, search_text),
        'accordion': render_accordion(request, course, discussion_info, discussion_id),
    }

    return render_to_response('discussion/index.html', context)

def render_single_thread(request, thread_id):
    context = {
        'thread': comment_client.get_thread(thread_id, recursive=True),
    }
    return render_to_string('discussion/single_thread.html', context)

def single_thread(request, thread_id):

    context = {
        'csrf': csrf(request)['csrf_token'],
        'init': '',
        'content': render_single_thread(request, thread_id),
        'accordion': '',
        'user_info': json.dumps(comment_client.get_user_info(request.user.id)),
    }

    return render_to_response('discussion/index.html', context)

def search(request):
    text = request.GET.get('text', None)
    threads = comment_client.search(text)
    context = {
        'csrf': csrf(request)['csrf_token'],
        'init': '',
        'content': render_discussion(request, threads, search_text=text),
        'accordion': '',
    }

    return render_to_response('discussion/index.html', context)
