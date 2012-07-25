from django.conf.urls.defaults import patterns, url

namespace_regex = r"[a-zA-Z\d._-]+"
article_slug = r'/(?P<article_path>' + namespace_regex + r'/[a-zA-Z\d_-]*)'
namespace = r'/(?P<namespace>' + namespace_regex + r')'

urlpatterns = patterns('',
        url(r'^$', 'simplewiki.views.root_redirect', name='wiki_root'),
        url(r'^view' + article_slug, 'simplewiki.views.view', name='wiki_view'),
        url(r'^view_revision/(?P<revision_number>[0-9]+)' + article_slug, 'simplewiki.views.view_revision', name='wiki_view_revision'),
        url(r'^edit' + article_slug, 'simplewiki.views.edit', name='wiki_edit'),
        url(r'^create' + article_slug, 'simplewiki.views.create', name='wiki_create'),
        url(r'^history' + article_slug + r'(?:/(?P<page>[0-9]+))?$', 'simplewiki.views.history', name='wiki_history'),
        url(r'^search_related' + article_slug, 'simplewiki.views.search_add_related', name='search_related'),
        url(r'^random/?$', 'simplewiki.views.random_article', name='wiki_random'),
        url(r'^revision_feed' + namespace + r'/(?P<page>[0-9]+)?$', 'simplewiki.views.revision_feed', name='wiki_revision_feed'),
        url(r'^search' + namespace + r'?$', 'simplewiki.views.search_articles', name='wiki_search_articles'),
        url(r'^list' + namespace + r'?$', 'simplewiki.views.search_articles', name='wiki_list_articles'),  # Just an alias for the search, but you usually don't submit a search term
)
