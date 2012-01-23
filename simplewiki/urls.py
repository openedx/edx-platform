from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'simplewiki.views.root_redirect', name='wiki_root'),
    url(r'^view(/[a-zA-Z\d/_-]*)/?$', 'simplewiki.views.view', name='wiki_view'),
    url(r'^edit(/[a-zA-Z\d/_-]*)/?$', 'simplewiki.views.edit', name='wiki_edit'),
    url(r'^create(/[a-zA-Z\d/_-]*)/?$', 'simplewiki.views.create', name='wiki_create'),
    url(r'^history(/[a-zA-Z\d/_-]*)/([0-9]*)/?$', 'simplewiki.views.history', name='wiki_history'),
    url(r'^search_related(/[a-zA-Z\d/_-]*)/?$', 'simplewiki.views.search_add_related', name='search_related'),
    url(r'^random/?$', 'simplewiki.views.random_article', name='wiki_random'),
    url(r'^search/?$', 'simplewiki.views.search_articles', name='wiki_search_articles'),    
    url(r'^list/?$', 'simplewiki.views.search_articles', name='wiki_list_articles'), #Just an alias for the search, but you usually don't submit a search term
#    url(r'^/?([a-zA-Z\d/_-]*)/_related/add/$', 'simplewiki.views.add_related', name='add_related'),
#    url(r'^/?([a-zA-Z\d/_-]*)/_related/remove/(\d+)$', 'simplewiki.views.remove_related', name='wiki_remove_relation'),
#    url(r'^/?([a-zA-Z\d/_-]*)/_add_attachment/$', 'simplewiki.views_attachments.add_attachment', name='add_attachment'),
#    url(r'^/?([a-zA-Z\d/_-]*)/_view_attachment/(.+)?$', 'simplewiki.views_attachments.view_attachment', name='wiki_view_attachment'),
#    url(r'^(.*)$', 'simplewiki.views.encode_err', name='wiki_encode_err')
)
