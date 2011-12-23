from django.conf.urls.defaults import patterns, include, url
import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^courseware/(?P<course>[^/]*)/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$', 'courseware.views.index'),
    url(r'^courseware/(?P<course>[^/]*)/(?P<chapter>[^/]*)/$', 'courseware.views.index'),
    url(r'^courseware/(?P<course>[^/]*)/$', 'courseware.views.index'),
#    url(r'^courseware/modx/(?P<id>[^/]*)/problem_check$', 'courseware.views.check_problem'),
    url(r'^modx/(?P<module>[^/]*)/(?P<id>[^/]*)/(?P<dispatch>[^/]*)$', 'courseware.views.modx_dispatch'), #reset_problem'),
    url(r'^courseware/$', 'courseware.views.index'),
    url(r'^profile$', 'courseware.views.profile'),
    url(r'^change_setting$', 'auth.views.change_setting'),
#    url(r'^admin/', include('django.contrib.admin.urls')),
#    url(r'^accounts/register/$', 'registration.views.register', {'success_url':'/accounts/register/complete'}),
#    url(r'^accounts/', include('registration.urls')),
    url(r'^t/(?P<template>[^/]*)$', 'static_template_view.views.index'),
    url(r'^textbook/(?P<filename>[^/]*)$', 'textbook.views.index'), 
    url(r'^logout$', 'auth.views.logout_user'),
    url(r'^login$', 'auth.views.login_user'),
    url(r'^login/(?P<error>[^/]*)$', 'auth.views.login_user'),
    url(r'^create_account$', 'auth.views.create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'auth.views.activate_account'),
    url(r'^$', 'auth.views.index'),
    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', 
        dict(from_email='6002-admin@mit.edu'),name='auth_password_reset'),
    url(r'^password_change/$',django.contrib.auth.views.password_change,name='auth_password_change'),
    url(r'^password_change_done/$',django.contrib.auth.views.password_change_done,name='auth_password_change_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',django.contrib.auth.views.password_reset_confirm,
        name='auth_password_reset_confirm'),
    url(r'^password_reset_complete/$',django.contrib.auth.views.password_reset_complete,
        name='auth_password_reset_complete'),
    url(r'^password_reset_done/$',django.contrib.auth.views.password_reset_done,
        name='auth_password_reset_done'),
#    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
#    url(r'^admin/', include(admin.site.urls)),
)
