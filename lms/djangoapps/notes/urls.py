from django.conf.urls import patterns, url


urlpatterns = patterns(
    'notes.api',
    url(
        r'^api$',
        'api_request',
        {
            'resource': 'root',
        },
        name='notes_api_root',
    ),
    url(
        r'^api/annotations$',
        'api_request',
        {
            'resource': 'notes',
        },
        name='notes_api_notes',
    ),
    url(
        r'^api/annotations/(?P<note_id>[0-9A-Fa-f]+)$',
        'api_request',
        {
            'resource': 'note',
        },
        name='notes_api_note',
    ),
    url(
        r'^api/search',
        'api_request',
        {
            'resource': 'search',
        },
        name='notes_api_search',
    ),
)
