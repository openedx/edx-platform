from django.conf import settings
from django.conf.urls import patterns, include, url

import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = ('',
    url(r'^$', 'contentstore.views.index', name='index'),
    url(r'^new_item$', 'contentstore.views.new_item', name='new_item'),
    url(r'^edit_item$', 'contentstore.views.edit_item', name='edit_item'),
    url(r'^save_item$', 'contentstore.views.save_item', name='save_item'),
    url(r'^clone_item$', 'contentstore.views.clone_item', name='clone_item'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<name>[^/]+)$',
        'contentstore.views.course_index', name='course_index'),
    url(r'^github_service_hook$', 'github_sync.views.github_post_receive'),
    url(r'^preview/modx/(?P<preview_id>[^/]*)/(?P<location>.*?)/(?P<dispatch>[^/]*)$',
        'contentstore.views.preview_dispatch', name='preview_dispatch')
)

# User creation and updating views
urlpatterns += (
    url(r'^signup$', 'contentstore.views.signup', name='signup'),

    url(r'^create_account$', 'student.views.create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account', name='activate'),

    # form page
    url(r'^login$', 'contentstore.views.login_page', name='login'),
    # ajax view that actually does the work
    url(r'^login_post$', 'student.views.login_user', name='login_post'),

    url(r'^logout$', 'student.views.logout_user', name='logout'),

    )

if settings.DEBUG:
    ## Jasmine
    urlpatterns=urlpatterns + (url(r'^_jasmine/', include('django_jasmine.urls')),)

urlpatterns = patterns(*urlpatterns)
