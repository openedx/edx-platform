"""
Views for accessing language preferences
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest, Http404
from django.core.urlresolvers import reverse
from util.json_request import expect_json, JsonResponse
from xmodule.modulestore.exceptions import ItemNotFoundError
from edxnotes.exceptions import EdxNotesError
from edxnotes.api import EdxNotes


# $.ajax({
#     type: 'POST',
#     data: JSON.stringify({'text': 'aaa'}),
#     url: 'http://localhost:8000/api/edxnotes/annotations/',
#     dataType:   "json",
#     contentType: "application/json; charset=utf-8",
#     success: function () {console.log(arguments)}
# })

# $.ajax({
#     type: 'GET|DELETE|PUT',
#     data: JSON.stringify({'text': 'aaa'}),
#     url: 'http://localhost:8000/api/edxnotes/annotations/1',
#     dataType:   "json",
#     contentType: "application/json; charset=utf-8",
#     success: function () {console.log(arguments)}
# })

# $.ajax({
#     type: 'GET',
#     data: JSON.stringify({'text': 'aaa'}),
#     url: 'http://localhost:8000/api/edxnotes/search',
#     dataType:   "json",
#     contentType: "application/json; charset=utf-8",
#     success: function () {console.log(arguments)}
# })


@require_http_methods(("DELETE", "GET", "PUT", "PATCH", "POST"))
@login_required
@expect_json
def note_handler(request, *args, **kwargs):
    note_id = kwargs.get('note_id')
    if request.method in ('POST', 'PUT', 'PATCH'):
        if note_id and 'id' in request.json:  # PUT, PATCH
            note = EdxNotes.update(note_id, request.json)
            return JsonResponse(note, status=200)
        else:  # POST
            note = EdxNotes.create(request.json)
            response = JsonResponse(note, status=201)
            response["Location"] = reverse(
                'note_handler', kwargs={'note_id': note['id']}
            )
            return response
    else:
        if not note_id:
            return HttpResponseBadRequest()

        try:
            if request.method == 'DELETE':
                EdxNotes.delete(note_id)
                return JsonResponse(status=204)
            else:  # 'GET'
                note = EdxNotes.read(note_id)
                return JsonResponse(note, status=200)
        except ItemNotFoundError:
            return Http404()


@require_http_methods("GET")
@login_required
@expect_json
def search_handler(request):
    user = request.GET.get('user')
    usage_id = request.GET.get('usageId')
    results = EdxNotes.search(user, usage_id)
    return JsonResponse(results, status=200)
