from django.http import HttpResponse, Http404
from django.core.exceptions import ValidationError
from notes.models import Note
import json
import logging

log = logging.getLogger(__name__)

#----------------------------------------------------------------------#
# API requests are routed through api_request() using the resource map.

def api_resource_map():
    ''' Maps API resources to (method, action) pairs. '''

    (GET, PUT, POST, DELETE) = ('GET', 'PUT', 'POST', 'DELETE') # for convenience

    return {
        'root': {GET: version},
        'notes': {GET: index, POST: create},
        'note': {GET: read, PUT: update, DELETE: delete},
        'search': {GET: search}
    }

def api_request(request, course_id, **kwargs):
    ''' Routes API requests to the appropriate action method and formats the results
        (defaults to JSON). 

        Raises a 404 if the resource type doesn't exist, or if there is no action 
            method associated with the HTTP method.
    '''
    resource_map = api_resource_map()
    resource_name = kwargs.pop('resource')
    resource = resource_map.get(resource_name)

    if resource is None:
        log.debug('Resource "{0}" does not exist'.format(resource_name))
        raise Http404

    if request.method not in resource.keys():
        log.debug('Resource "{0}" does not support method "{1}"'.format(resource_name, request.method)) 
        raise Http404

    log.debug("API request: {0} {1}".format(request.method, resource_name))

    action = resource.get(request.method)
    result = action(request, course_id, **kwargs)

    response = result[0]
    data = None
    if len(result) == 2: 
        data = result[1]

    formatted = api_format(request, response, data)
    response['Content-type'] = formatted[0]
    response.content = formatted[1]

    log.debug("API response:")
    log.debug(response)

    return response

def api_format(request, response, data):
    ''' Returns a two-element list containing the content type and content. 
        This method does not modify the request or response.
    ''' 
    content_type = 'application/json'
    if data is None:
        content = ''
    else:
        content = json.dumps(data)
    return [content_type, content]

#----------------------------------------------------------------------#
# Exposed API actions via the resource map.

def index(request, course_id):
    notes = Note.objects.filter(course_id=course_id, user=request.user)
    return [HttpResponse(), [note.as_dict() for note in notes]]

def create(request, course_id):
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
    try:
        note = Note.objects.get(id=note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    return [HttpResponse(), note.as_dict()]

def update(request, course_id, note_id):
    try:
        note = Note.objects.get(note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    try:
        note.clean(request.body)
    except ValidationError as e:
        log.debug(e)
        return [HttpResponse('', status=500), None]

    note.save(update_fields=['text', 'tags', 'updated'])

    return [HttpResponse('', status=303), None]

def delete(request, course_id, note_id):
    try:
        note = Note.objects.get(note_id)
    except:
        return [HttpResponse('', status=404), None]

    if not note.user.id == request.user.id:
        return [HttpResponse('', status=403)]

    note.delete()

    return [HttpResponse('', status=204), None]

def search(request, course_id):
    limit = request.GET.get('limit')
    uri = request.GET.get('uri')

    filters = {'course_id':course_id, 'user':request.user}
    if uri is not None:
        filters['uri'] = uri

    notes = Note.objects.filter(**filters)
    #if limit is not None and limit > 0:
        #notes = notes[:limit]

    result = {'rows': [note.as_dict() for note in notes]}

    return [HttpResponse(), result]

def version(request, course_id):
    return [HttpResponse(), {'name': 'Notes API', 'version': '1.0'}]
