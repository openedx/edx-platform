from importlib import import_module
from courseware.models import StudentModuleCache
from courseware.module_render import get_module
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from django.http import HttpResponse
from django.utils import simplejson

from django.conf import settings
import operator
import itertools

from django_comment_client.permissions import check_permissions_by_view

_FULLMODULES = None
_DISCUSSIONINFO = None

def extract(dic, keys):
    return {k: dic.get(k) for k in keys}

def strip_none(dic):
    def _is_none(v):
        return v is None or (isinstance(v, str) and len(v.strip()) == 0)
    return dict([(k, v) for k, v in dic.iteritems() if not _is_none(v)])

def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())

def get_full_modules():
    global _FULLMODULES
    if not _FULLMODULES:
        class_path = settings.MODULESTORE['default']['ENGINE']
        module_path, _, class_name = class_path.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        modulestore = class_(**dict(settings.MODULESTORE['default']['OPTIONS'].items() + [('eager', True)]))
        _FULLMODULES = modulestore.modules
    return _FULLMODULES

def get_categorized_discussion_info(request, course):
    """
        return a dict of the form {category: modules}
    """
    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO:
        initialize_discussion_info(request, course)
    return _DISCUSSIONINFO['categorized']

def get_discussion_title(request, course, discussion_id):
    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO:
        initialize_discussion_info(request, course)
    title = _DISCUSSIONINFO['by_id'].get(discussion_id, {}).get('title', '(no title)')
    return title

def initialize_discussion_info(request, course):

    global _DISCUSSIONINFO
    if _DISCUSSIONINFO:
        return

    course_id = course.id
    _, course_name, _ = course_id.split('/')
    user = request.user
    url_course_id = course_id.replace('/', '_').replace('.', '_')

    _is_course_discussion = lambda x: x[0].dict()['category'] == 'discussion' \
                         and x[0].dict()['course'] == course_name
    
    _get_module_descriptor = operator.itemgetter(1)

    def _get_module(module_descriptor):
        print module_descriptor
        module = get_module(user, request, module_descriptor.location, student_module_cache)
        return module

    def _extract_info(module):
        return {
            'title': module.title,
            'discussion_id': module.discussion_id,
            'category': module.discussion_category,
        }

    def _pack_with_id(info):
        return (info['discussion_id'], info)

    discussion_module_descriptors = map(_get_module_descriptor,
                                        filter(_is_course_discussion,
                                               get_full_modules().items()))

    student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(user, course)

    discussion_info = map(_extract_info, map(_get_module, discussion_module_descriptors))

    _DISCUSSIONINFO = {}

    _DISCUSSIONINFO['by_id'] = dict(map(_pack_with_id, discussion_info))

    _DISCUSSIONINFO['categorized'] = dict((category, list(l)) \
                for category, l in itertools.groupby(discussion_info, operator.itemgetter('category')))

    _DISCUSSIONINFO['categorized']['General'] = [{
        'title': 'General discussion',
        'discussion_id': url_course_id,
        'category': 'General',
    }]

class JsonResponse(HttpResponse):
    def __init__(self, data=None):
        content = simplejson.dumps(data)
        super(JsonResponse, self).__init__(content,
                                           mimetype='application/json; charset=utf8')

class JsonError(HttpResponse):
    def __init__(self, error_messages=[]):
        if isinstance(error_messages, str):
            error_messages = [error_messages]
        content = simplejson.dumps({'errors': error_messages},
                                   indent=2,
                                   ensure_ascii=False)
        super(JsonError, self).__init__(content,
                                        mimetype='application/json; charset=utf8', status=400)

class HtmlResponse(HttpResponse):
    def __init__(self, html=''):
        super(HtmlResponse, self).__init__(html, content_type='text/plain')

class ViewNameMiddleware(object):  
    def process_view(self, request, view_func, view_args, view_kwargs):  
        request.view_name = view_func.__name__

def get_annotated_content_info(course_id, content, user, type):
    return {
        'editable': check_permissions_by_view(user, course_id, content, "update_thread" if type == 'thread' else "update_comment"),
        'can_reply': check_permissions_by_view(user, course_id, content, "create_comment" if type == 'thread' else "create_sub_comment"),
        'can_endorse': check_permissions_by_view(user, course_id, content, "endorse_comment") if type == 'comment' else False,
        'can_delete': check_permissions_by_view(user, course_id, content, "delete_thread" if type == 'thread' else "delete_comment"),
        'can_openclose': check_permissions_by_view(user, course_id, content, "openclose_thread") if type == 'thread' else False,
    }

def get_annotated_content_infos(course_id, thread, user, type='thread'):
    infos = {}
    def _annotate(content, type):
        infos[str(content['id'])] = get_annotated_content_info(course_id, content, user, type)
        for child in content.get('children', []):
            _annotate(child, 'comment')
    _annotate(thread, type)
    return infos

def pluralize(singular_term, count):
    if int(count) >= 2:
        return singular_term + 's'
    return singular_term

