from django.conf.urls import url, patterns

urlpatterns = patterns('',  # nopep8
    url(r'^annotations/(?P<note_id>.+)?$', 'edxnotes.views.note_handler', name='note_handler'),
    url(r'^search$', 'edxnotes.views.search_handler', name='search_handler'),
)
