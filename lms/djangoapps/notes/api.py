from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.core.exceptions import ValidationError

from notes.models import Note
from notes.utils import notes_enabled_for_course
from courseware.courses import get_course_with_access

import json
import logging
import collections

log = logging.getLogger(__name__)

API_SETTINGS = {
    'META': {'name': 'Notes API', 'version': 1},

    # Maps resources to HTTP methods and actions
    'RESOURCE_MAP': {
        'root': {'GET': 'root'},
        'notes': {'GET': 'index', 'POST': 'create'},
        'note': {'GET': 'read', 'PUT': 'update', 'DELETE': 'delete'},
        'search': {'GET': 'search'},
    },

    # Cap the number of notes that can be returned in one request
    'MAX_NOTE_LIMIT': 1000,
}

# Wrapper class for HTTP response and data. All API actions are expected to return this.
ApiResponse = collections.namedtuple('ApiResponse', ['http_response', 'data'])

#----------------------------------------------------------------------#
# API requests are routed through api_request() using the resource map.


def api_enabled(request, course_key):
    '''
    Returns True if the api is enabled for the course, otherwise False.
    '''
    course = _get_course(request, course_key)
    return notes_enabled_for_course(course)


@login_required
def api_request(request, course_id, **kwargs):
    '''
    Routes API requests to the appropriate action method and returns JSON.
    Raises a 404 if the requested resource does not exist or notes are
        disabled for the course.
    '''
    assert isinstance(course_id, basestring)
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    # Verify that the api should be accessible to this course
    if not api_enabled(request, course_key):
        log.debug('Notes are disabled for course: {0}'.format(course_id))
        raise Http404

    # Locate the requested resource
    resource_map = API_SETTINGS.get('RESOURCE_MAP', {})
    resource_name = kwargs.pop('resource')
    resource_method = request.method
    resource = resource_map.get(resource_name)

    if resource is None:
        log.debug('Resource "{0}" does not exist'.format(resource_name))
        raise Http404

    if resource_method not in resource.keys():
        log.debug('Resource "{0}" does not support method "{1}"'.format(resource_name, resource_method))
        raise Http404

    # Execute the action associated with the resource
    func = resource.get(resource_method)
    module = globals()
    if func not in module:
        log.debug('Function "{0}" does not exist for request {1} {2}'.format(func, resource_method, resource_name))
        raise Http404

    log.debug('API request: {0} {1}'.format(resource_method, resource_name))

    api_response = module[func](request, course_key, **kwargs)
    http_response = api_format(api_response)

    return http_response


def api_format(api_response):
    '''
    Takes an ApiResponse and returns an HttpResponse.
    '''
    http_response = api_response.http_response
    content_type = 'application/json'
    content = ''

    # not doing a strict boolean check on data becuase it could be an empty list
    if api_response.data is not None and api_response.data != '':
        content = json.dumps(api_response.data)

    http_response['Content-type'] = content_type
    http_response.content = content

    log.debug('API response type: {0} content: {1}'.format(content_type, content))

    return http_response


def _get_course(request, course_key):
    '''
    Helper function to load and return a user's course.
    '''
    return get_course_with_access(request.user, 'load', course_key)

#----------------------------------------------------------------------#
# API actions exposed via the resource map.


def index(request, course_key):
    '''
    Returns a list of annotation objects.
    '''
    MAX_LIMIT = API_SETTINGS.get('MAX_NOTE_LIMIT')

    notes = Note.objects.order_by('id').filter(course_id=course_key,
                                               user=request.user)[:MAX_LIMIT]

    return ApiResponse(http_response=HttpResponse(), data=[note.as_dict() for note in notes])


def create(request, course_key):
    '''
    Receives an annotation object to create and returns a 303 with the read location.
    '''
    note = Note(course_id=course_key, user=request.user)

    try:
        note.clean(request.body)
    except ValidationError as e:
        log.debug(e)
        return ApiResponse(http_response=HttpResponse('', status=400), data=None)

    note.save()
    response = HttpResponse('', status=303)
    response['Location'] = note.get_absolute_url()

    return ApiResponse(http_response=response, data=None)


def read(request, _course_key, note_id):
    '''
    Returns a single annotation object.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return ApiResponse(http_response=HttpResponse('', status=404), data=None)

    if note.user.id != request.user.id:
        return ApiResponse(http_response=HttpResponse('', status=403), data=None)

    return ApiResponse(http_response=HttpResponse(), data=note.as_dict())


def update(request, course_key, note_id):  # pylint: disable=unused-argument
    '''
    Updates an annotation object and returns a 303 with the read location.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return ApiResponse(http_response=HttpResponse('', status=404), data=None)

    if note.user.id != request.user.id:
        return ApiResponse(http_response=HttpResponse('', status=403), data=None)

    try:
        note.clean(request.body)
    except ValidationError as e:
        log.debug(e)
        return ApiResponse(http_response=HttpResponse('', status=400), data=None)

    note.save()

    response = HttpResponse('', status=303)
    response['Location'] = note.get_absolute_url()

    return ApiResponse(http_response=response, data=None)


def delete(request, course_id, note_id):
    '''
    Deletes the annotation object and returns a 204 with no content.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return ApiResponse(http_response=HttpResponse('', status=404), data=None)

    if note.user.id != request.user.id:
        return ApiResponse(http_response=HttpResponse('', status=403), data=None)

    note.delete()

    return ApiResponse(http_response=HttpResponse('', status=204), data=None)


def search(request, course_key):
    '''
    Returns a subset of  annotation objects based on a search query.
    '''
    MAX_LIMIT = API_SETTINGS.get('MAX_NOTE_LIMIT')

    # search parameters
    offset = request.GET.get('offset', '')
    limit = request.GET.get('limit', '')
    uri = request.GET.get('uri', '')

    # validate search parameters
    if offset.isdigit():
        offset = int(offset)
    else:
        offset = 0

    if limit.isdigit():
        limit = int(limit)
        if limit == 0 or limit > MAX_LIMIT:
            limit = MAX_LIMIT
    else:
        limit = MAX_LIMIT

    # set filters
    filters = {'course_id': course_key, 'user': request.user}
    if uri != '':
        filters['uri'] = uri

    # retrieve notes
    notes = Note.objects.order_by('id').filter(**filters)
    total = notes.count()
    rows = notes[offset:offset + limit]
    result = {
        'total': total,
        'rows': [note.as_dict() for note in rows]
    }

    return ApiResponse(http_response=HttpResponse(), data=result)


def root(request, course_key):  # pylint: disable=unused-argument
    '''
    Returns version information about the API.
    '''
    return ApiResponse(http_response=HttpResponse(), data=API_SETTINGS.get('META'))
