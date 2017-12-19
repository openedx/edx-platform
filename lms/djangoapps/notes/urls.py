"""
URL definitions for the notes app
"""

from django.conf.urls import url

from notes.api import api_request

id_regex = r"(?P<note_id>[0-9A-Fa-f]+)"
urlpatterns = [
    url(r'^api$', api_request, {'resource': 'root'}, name='notes_api_root'),
    url(r'^api/annotations$', api_request, {'resource': 'notes'}, name='notes_api_notes'),
    url(r'^api/annotations/' + id_regex + r'$', api_request, {'resource': 'note'}, name='notes_api_note'),
    url(r'^api/search', api_request, {'resource': 'search'}, name='notes_api_search')
]
