from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.core.exceptions import ValidationError
from notes.models import Note
from notes.utils import notes_enabled_for_course
from courseware.courses import get_course_with_access
import json
import logging

log = logging.getLogger(__name__)

API_SETTINGS = {
    # Version
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

#----------------------------------------------------------------------#
# API requests are routed through api_request() using the resource map.


def api_enabled(request, course_id):
    '''
    Returns True if the api is enabled for the course, otherwise False.
    '''
    course = _get_course(request, course_id)
    return notes_enabled_for_course(course)


@login_required
def api_request(request, course_id, **kwargs):
    '''
    Routes API requests to the appropriate action method and returns JSON.
    Raises a 404 if the requested resource does not exist or notes are
        disabled for the course.
    '''

    # Verify that the api should be accessible to this course
    if not api_enabled(request, course_id):
        log.debug('Notes not enabled for course')
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
    result = module[func](request, course_id, **kwargs)

    # Format and output the results
    data = None
    response = result[0]
    if len(result) == 2:
        data = result[1]

    formatted = api_format(request, response, data)
    response['Content-type'] = formatted[0]
    response.content = formatted[1]

    log.debug('API response: {0}'.format(formatted))

    return response


def api_format(request, response, data):
    '''
    Returns a two-element list containing the content type and content.
    '''
    content_type = 'application/json'
    if data is None:
        content = ''
    else:
        content = json.dumps(data)
    return [content_type, content]


def _get_course(request, course_id):
    '''
    Helper function to load and return a user's course.
    '''
    return get_course_with_access(request.user, course_id, 'load')

#----------------------------------------------------------------------#
# API actions exposed via the resource map.


def index(request, course_id):
    '''
    Returns a list of annotation objects.
    '''
    MAX_LIMIT = API_SETTINGS.get('MAX_NOTE_LIMIT')

    notes = Note.objects.order_by('id').filter(course_id=course_id,
                                               user=request.user)[:MAX_LIMIT]

    return [HttpResponse(), [note.as_dict() for note in notes]]


def create(request, course_id):
    '''
    Receives an annotation object to create and returns a 303 with the read location.
    '''
    note = Note(course_id=course_id, user=request.user)

    try:
        note.clean(request.body)
    except ValidationError as e:
        log.debug(e)
        return [HttpResponse('', status=500), None]

    note.save()
    response = HttpResponse('', status=303)
    response['Location'] = note.get_absolute_url()

    return [response, None]


def read(request, course_id, note_id):
    '''
    Returns a single annotation object.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    return [HttpResponse(), note.as_dict()]


def update(request, course_id, note_id):
    '''
    Updates an annotation object and returns a 303 with the read location.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    try:
        note.clean(request.body)
    except ValidationError as e:
        log.debug(e)
        return [HttpResponse('', status=500), None]

    note.save()

    response = HttpResponse('', status=303)
    response['Location'] = note.get_absolute_url()

    return [response, None]


def delete(request, course_id, note_id):
    '''
    Deletes the annotation object and returns a 204 with no content.
    '''
    try:
        note = Note.objects.get(id=note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    note.delete()

    return [HttpResponse('', status=204), None]


def search(request, course_id):
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
    filters = {'course_id': course_id, 'user': request.user}
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

    return [HttpResponse(), result]


def root(request, course_id):
    '''
    Returns version information about the API.
    '''
    return [HttpResponse(), API_SETTINGS.get('META')]
