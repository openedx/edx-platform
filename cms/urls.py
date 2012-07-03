from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'contentstore.views.index', name='index'),
    url(r'^edit_item$', 'contentstore.views.edit_item', name='edit_item'),
    url(r'^save_item$', 'contentstore.views.save_item', name='save_item'),
    url(r'^temp_force_export$', 'contentstore.views.temp_force_export'),
    url(r'^github_service_hook$', 'github_sync.views.github_post_receive'),
)
