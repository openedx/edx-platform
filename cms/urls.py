from django.conf import settings
from django.conf.urls import patterns, include, url

import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = ('',
    url(r'^$', 'contentstore.views.index', name='index'),
    url(r'^edit/(?P<location>.*?)$', 'contentstore.views.edit_unit', name='edit_unit'),
    url(r'^subsection/(?P<location>.*?)$', 'contentstore.views.edit_subsection', name='edit_subsection'),
    url(r'^preview_component/(?P<location>.*?)$', 'contentstore.views.preview_component', name='preview_component'),
    url(r'^save_item$', 'contentstore.views.save_item', name='save_item'),
    url(r'^delete_item$', 'contentstore.views.delete_item', name='delete_item'),
    url(r'^clone_item$', 'contentstore.views.clone_item', name='clone_item'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<name>[^/]+)$',
        'contentstore.views.course_index', name='course_index'),
    url(r'^github_service_hook$', 'github_sync.views.github_post_receive'),
    url(r'^preview/modx/(?P<preview_id>[^/]*)/(?P<location>.*?)/(?P<dispatch>[^/]*)$',
        'contentstore.views.preview_dispatch', name='preview_dispatch'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<coursename>[^/]+)/upload_asset$', 
        'contentstore.views.upload_asset', name='upload_asset'),
    url(r'^manage_users/(?P<location>.*?)$', 'contentstore.views.manage_users', name='manage_users'),
    url(r'^add_user/(?P<location>.*?)$',
        'contentstore.views.add_user', name='add_user'),
    url(r'^remove_user/(?P<location>.*?)$',
        'contentstore.views.remove_user', name='remove_user'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<name>[^/]+)/remove_user$',
        'contentstore.views.remove_user', name='remove_user'),
    url(r'^assets/(?P<location>.*?)$', 'contentstore.views.asset_index', name='asset_index'),

    # temporary landing page for a course
    url(r'^landing/(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<coursename>[^/]+)$', 'contentstore.views.landing', name='landing')

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
