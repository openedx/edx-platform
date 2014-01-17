from django.conf.urls import patterns, url


id_regex = r"(?P<note_id>[0-9A-Fa-f]+)"
urlpatterns = patterns('notes.api',
                       url(r'^api$', 'api_request', {'resource': 'root'}, name='notes_api_root'),
                       url(r'^api/annotations$', 'api_request', {'resource': 'notes'}, name='notes_api_notes'),
                       url(r'^api/annotations/' + id_regex + r'$', 'api_request', {'resource': 'note'}, name='notes_api_note'),
                       url(r'^api/search', 'api_request', {'resource': 'search'}, name='notes_api_search')
                       )
