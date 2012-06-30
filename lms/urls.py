from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
if settings.DEBUG:
    from django.contrib import admin
    admin.autodiscover()

urlpatterns = ('',
    url(r'^$', 'student.views.index', name="root"), # Main marketing page, or redirect to courseware
    url(r'^about$', 'student.views.about', name="about_edx"),
    url(r'^jobs$', 'student.views.jobs', name="jobs"),
    url(r'^help$', 'student.views.help', name="help_edx"),
    url(r'^dashboard$', 'student.views.dashboard', name="dashboard"),
    url(r'^change_email$', 'student.views.change_email_request'),
    url(r'^email_confirm/(?P<key>[^/]*)$', 'student.views.confirm_email_change'),
    url(r'^change_name$', 'student.views.change_name_request'),
    url(r'^accept_name_change$', 'student.views.accept_name_change'),
    url(r'^reject_name_change$', 'student.views.reject_name_change'),
    url(r'^pending_name_changes$', 'student.views.pending_name_changes'),
    url(r'^gradebook$', 'courseware.views.gradebook'),
    url(r'^event$', 'track.views.user_track'),
    url(r'^t/(?P<template>[^/]*)$', 'static_template_view.views.index'),
    url(r'^login$', 'student.views.login_user'),
    url(r'^login/(?P<error>[^/]*)$', 'student.views.login_user'),
    url(r'^logout$', 'student.views.logout_user', name='logout'),
    url(r'^create_account$', 'student.views.create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account'),
#    url(r'^reactivate/(?P<key>[^/]*)$', 'student.views.reactivation_email'),
    url(r'^password_reset/$', 'student.views.password_reset'),
    ## Obsolete Django views for password resets
    ## TODO: Replace with Mako-ized views
    url(r'^password_change/$',django.contrib.auth.views.password_change,name='auth_password_change'),
    url(r'^password_change_done/$',django.contrib.auth.views.password_change_done,name='auth_password_change_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',django.contrib.auth.views.password_reset_confirm,
        name='auth_password_reset_confirm'),
    url(r'^password_reset_complete/$',django.contrib.auth.views.password_reset_complete,
        name='auth_password_reset_complete'),
    url(r'^password_reset_done/$',django.contrib.auth.views.password_reset_done,
        name='auth_password_reset_done'),
    ## Feedback
    url(r'^send_feedback$', 'util.views.send_feedback'),
)

if settings.PERFSTATS:
    urlpatterns += (url(r'^reprofile$','perfstats.views.end_profile'),)

if settings.COURSEWARE_ENABLED:
    urlpatterns += (
        url(r'^masquerade/', include('masquerade.urls')),
        url(r'^courseware/(?P<course>[^/]*)/(?P<chapter>[^/]*)/(?P<section>[^/]*)/(?P<position>[^/]*)$', 'courseware.views.index'),
        # url(r'^courseware/(?P<course>[^/]*)/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$', 'courseware.views.index', name="courseware_section"),
        url(r'^courseware/(?P<course>[^/]*)/(?P<chapter>[^/]*)/$', 'courseware.views.index', name="courseware_chapter"),
        url(r'^courseware/(?P<course>[^/]*)/$', 'courseware.views.index', name="courseware_course"),
        url(r'^jumpto/(?P<probname>[^/]+)/$', 'courseware.views.jump_to'),
        url(r'^section/(?P<section>[^/]*)/$', 'courseware.views.render_section'),
        url(r'^modx/(?P<module>[^/]*)/(?P<id>[^/]*)/(?P<dispatch>[^/]*)$', 'courseware.module_render.modx_dispatch'), #reset_problem'),
        url(r'^change_setting$', 'student.views.change_setting'),
        url(r'^s/(?P<template>[^/]*)$', 'static_template_view.views.auth_index'),
        url(r'^book/(?P<page>[^/]*)$', 'staticbook.views.index'),
        url(r'^book-shifted/(?P<page>[^/]*)$', 'staticbook.views.index_shifted'),
        url(r'^book*$', 'staticbook.views.index'),
        #    url(r'^course_info/$', 'student.views.courseinfo'),
        #    url(r'^show_circuit/(?P<circuit>[^/]*)$', 'circuit.views.show_circuit'),
        url(r'^edit_circuit/(?P<circuit>[^/]*)$', 'circuit.views.edit_circuit'),
        url(r'^save_circuit/(?P<circuit>[^/]*)$', 'circuit.views.save_circuit'),
        url(r'^calculate$', 'util.views.calculate'),
        url(r'^heartbeat$', include('heartbeat.urls')),

        # Multicourse related:
        url(r'^courses/?$', 'courseware.views.courses', name="courses"),
        url(r'^courses/(?P<course_id>[^/]*)/info$', 'util.views.info', name="info"),
        url(r'^courses/(?P<course_id>[^/]*)/book$', 'staticbook.views.index', name="book"),
        url(r'^courses/(?P<course_id>[^/]*)/enroll$', 'student.views.enroll', name="enroll"),
        url(r'^courses/(?P<course_id>[^/]*)/courseware/?$', 'courseware.views.index', name="courseware"),
        url(r'^courses/(?P<course_id>[^/]*)/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$', 'courseware.views.index', name="courseware_section"),
        url(r'^courses/(?P<course_id>[^/]*)/profile$', 'courseware.views.profile', name="profile"),
        url(r'^courses/(?P<course_id>[^/]*)/profile/(?P<student_id>[^/]*)/$', 'courseware.views.profile'),

        url(r'^courses/(?P<course_id>[^/]*)/about$', 'courseware.views.course_info', name="about_course"),
    )
    
    # Multicourse wiki
    article_slug = r"/(?P<article_path>[a-zA-Z\d_-]+/[a-zA-Z\d_-]*)"
    urlpatterns += (
        url(r'^courses/(?P<course_id>[^/]*)/wiki/$', 'simplewiki.views.root_redirect', name='wiki_root'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/view' + article_slug + r'/?$', 'simplewiki.views.view', name='wiki_view'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/view_revision/(?P<revision_number>[0-9]+)' + article_slug + r'/?$', 'simplewiki.views.view_revision', name='wiki_view_revision'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/edit' + article_slug + r'/?$', 'simplewiki.views.edit', name='wiki_edit'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/create/?$', 'simplewiki.views.create', name='wiki_create'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/history' + article_slug + r'(?:/(?P<page>[0-9]+))?/?$', 'simplewiki.views.history', name='wiki_history'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/search_related' + article_slug + r'/?$', 'simplewiki.views.search_add_related', name='search_related'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/random/?$', 'simplewiki.views.random_article', name='wiki_random'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/revision_feed/([0-9]+)/?$', 'simplewiki.views.revision_feed', name='wiki_revision_feed'),
        url(r'^courses/(?P<course_id>[^/]*)/wiki/search/?$', 'simplewiki.views.search_articles', name='wiki_search_articles'),    
        url(r'^courses/(?P<course_id>[^/]*)/wiki/list/?$', 'simplewiki.views.search_articles', name='wiki_list_articles'), #Just an alias for the search, but you usually don't submit a search term
    
    
    )
    

if settings.ENABLE_MULTICOURSE:
	urlpatterns += (url(r'^mitxhome$', 'multicourse.views.mitxhome'),)

if settings.QUICKEDIT:
	urlpatterns += (url(r'^quickedit/(?P<id>[^/]*)$', 'dogfood.views.quickedit'),)
	urlpatterns += (url(r'^dogfood/(?P<id>[^/]*)$', 'dogfood.views.df_capa_problem'),)

if settings.ASKBOT_ENABLED:
    urlpatterns += (url(r'^%s' % settings.ASKBOT_URL, include('askbot.urls')), \
                    url(r'^admin/', include(admin.site.urls)), \
                    url(r'^settings/', include('askbot.deps.livesettings.urls')), \
                    url(r'^followit/', include('followit.urls')), \
#                       url(r'^robots.txt$', include('robots.urls')),
                              )

if settings.DEBUG:
    ## Jasmine
    urlpatterns=urlpatterns + (url(r'^_jasmine/', include('django_jasmine.urls')),)

urlpatterns = patterns(*urlpatterns)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
