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

_FULLMODULES = None
_DISCUSSIONINFO = None

def extract(dic, keys):
    return {k: dic[k] for k in keys}

def strip_none(dic):
    def _is_none(v):
        return v is None or (isinstance(v, str) and len(v.strip()) == 0)
    return dict([(k, v) for k, v in dic.iteritems() if not _is_none(v)])

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
        module = get_module(user, request, module_descriptor.location, student_module_cache)[0]
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

    student_module_cache = StudentModuleCache(user, course)

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
        content = simplejson.dumps(data,
                                   indent=2,
                                   ensure_ascii=False)
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
                                        mimetype='application/json; charset=utf8')
