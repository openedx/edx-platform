from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static
import django.contrib.auth.views

# Uncomment the next two lines to enable the admin:
if settings.DEBUG:
    from django.contrib import admin
    admin.autodiscover()

urlpatterns = ('',
    url(r'^$', 'branding.views.index', name="root"), # Main marketing page, or redirect to courseware
    url(r'^dashboard$', 'student.views.dashboard', name="dashboard"),

    url(r'^admin_dashboard$', 'dashboard.views.dashboard'),

    # Adding to allow debugging issues when prod is mysteriously different from staging
    # (specifically missing get parameters in certain cases)
    url(r'^debug_request$', 'util.views.debug_request'),

    url(r'^change_email$', 'student.views.change_email_request'),
    url(r'^email_confirm/(?P<key>[^/]*)$', 'student.views.confirm_email_change'),
    url(r'^change_name$', 'student.views.change_name_request'),
    url(r'^accept_name_change$', 'student.views.accept_name_change'),
    url(r'^reject_name_change$', 'student.views.reject_name_change'),
    url(r'^pending_name_changes$', 'student.views.pending_name_changes'),

    url(r'^event$', 'track.views.user_track'),
    url(r'^t/(?P<template>[^/]*)$', 'static_template_view.views.index'), # TODO: Is this used anymore? What is STATIC_GRAB?

    url(r'^login$', 'student.views.login_user', name="login"),
    url(r'^login/(?P<error>[^/]*)$', 'student.views.login_user'),
    url(r'^logout$', 'student.views.logout_user', name='logout'),
    url(r'^create_account$', 'student.views.create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account', name="activate"),

    url(r'^password_reset/$', 'student.views.password_reset', name='password_reset'),
    ## Obsolete Django views for password resets
    ## TODO: Replace with Mako-ized views
    url(r'^password_change/$', django.contrib.auth.views.password_change,
        name='auth_password_change'),
    url(r'^password_change_done/$', django.contrib.auth.views.password_change_done,
        name='auth_password_change_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        django.contrib.auth.views.password_reset_confirm,
        name='auth_password_reset_confirm'),
    url(r'^password_reset_complete/$', django.contrib.auth.views.password_reset_complete,
        name='auth_password_reset_complete'),
    url(r'^password_reset_done/$', django.contrib.auth.views.password_reset_done,
        name='auth_password_reset_done'),

    url(r'^heartbeat$', include('heartbeat.urls')),

    url(r'^university_profile/(?P<org_id>[^/]+)$', 'courseware.views.university_profile', name="university_profile"),

    #Semi-static views (these need to be rendered and have the login bar, but don't change)
    url(r'^404$', 'static_template_view.views.render',
        {'template': '404.html'}, name="404"),
    url(r'^about$', 'static_template_view.views.render',
        {'template': 'about.html'}, name="about_edx"),
    url(r'^jobs$', 'static_template_view.views.render',
        {'template': 'jobs.html'}, name="jobs"),
    url(r'^contact$', 'static_template_view.views.render',
        {'template': 'contact.html'}, name="contact"),
    url(r'^press$', 'student.views.press', name="press"),
    url(r'^faq$', 'static_template_view.views.render',
        {'template': 'faq.html'}, name="faq_edx"),
    url(r'^help$', 'static_template_view.views.render',
        {'template': 'help.html'}, name="help_edx"),

    url(r'^tos$', 'static_template_view.views.render',
        {'template': 'tos.html'}, name="tos"),
    url(r'^privacy$', 'static_template_view.views.render',
        {'template': 'privacy.html'}, name="privacy_edx"),
    # TODO: (bridger) The copyright has been removed until it is updated for edX
    # url(r'^copyright$', 'static_template_view.views.render',
    #     {'template': 'copyright.html'}, name="copyright"),
    url(r'^honor$', 'static_template_view.views.render',
        {'template': 'honor.html'}, name="honor"),

    #Press releases
    url(r'^press/mit-and-harvard-announce-edx$', 'static_template_view.views.render',
        {'template': 'press_releases/MIT_and_Harvard_announce_edX.html'}, name="press/mit-and-harvard-announce-edx"),
    url(r'^press/uc-berkeley-joins-edx$', 'static_template_view.views.render',
        {'template': 'press_releases/UC_Berkeley_joins_edX.html'}, name="press/uc-berkeley-joins-edx"),
    url(r'^press/edX-announces-proctored-exam-testing$', 'static_template_view.views.render',
        {'template': 'press_releases/edX_announces_proctored_exam_testing.html'}, name="press/edX-announces-proctored-exam-testing"),

    # Should this always update to point to the latest press release?
    (r'^pressrelease$', 'django.views.generic.simple.redirect_to', {'url': '/press/uc-berkeley-joins-edx'}),


    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/static/images/favicon.ico'}),

    # TODO: These urls no longer work. They need to be updated before they are re-enabled
    # url(r'^send_feedback$', 'util.views.send_feedback'),
    # url(r'^reactivate/(?P<key>[^/]*)$', 'student.views.reactivation_email'),
)

if settings.PERFSTATS:
    urlpatterns += (url(r'^reprofile$','perfstats.views.end_profile'),)



# Multicourse wiki (Note: wiki urls must be above the courseware ones because of
# the custom tab catch-all)
if settings.WIKI_ENABLED:
    from wiki.urls import get_pattern as wiki_pattern
    from django_notify.urls import get_pattern as notify_pattern

    # Note that some of these urls are repeated in course_wiki.course_nav. Make sure to update
    # them together.
    urlpatterns += (
        # First we include views from course_wiki that we use to override the default views.
        # They come first in the urlpatterns so they get resolved first
        url('^wiki/create-root/$', 'course_wiki.views.root_create', name='root_create'),


        url(r'^wiki/', include(wiki_pattern())),
        url(r'^notify/', include(notify_pattern())),

        # These urls are for viewing the wiki in the context of a course. They should
        # never be returned by a reverse() so they come after the other url patterns
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/course_wiki/?$',
            'course_wiki.views.course_wiki_redirect', name="course_wiki"),
        url(r'^courses/(?:[^/]+/[^/]+/[^/]+)/wiki/', include(wiki_pattern())),
    )


if settings.COURSEWARE_ENABLED:
    urlpatterns += (
        # Hook django-masquerade, allowing staff to view site as other users
        url(r'^masquerade/', include('masquerade.urls')),

        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/jump_to/(?P<location>.*)$',
            'courseware.views.jump_to', name="jump_to"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/modx/(?P<location>.*?)/(?P<dispatch>[^/]*)$',
            'courseware.module_render.modx_dispatch',
            name='modx_dispatch'),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/xqueue/(?P<userid>[^/]*)/(?P<id>.*?)/(?P<dispatch>[^/]*)$',
            'courseware.module_render.xqueue_callback',
            name='xqueue_callback'),
        url(r'^change_setting$', 'student.views.change_setting',
            name='change_setting'),

        # TODO: These views need to be updated before they work
        url(r'^calculate$', 'util.views.calculate'),
        # TODO: We should probably remove the circuit package. I believe it was only used in the old way of saving wiki circuits for the wiki
        # url(r'^edit_circuit/(?P<circuit>[^/]*)$', 'circuit.views.edit_circuit'),
        # url(r'^save_circuit/(?P<circuit>[^/]*)$', 'circuit.views.save_circuit'),

        url(r'^courses/?$', 'branding.views.courses', name="courses"),
        url(r'^change_enrollment$',
            'student.views.change_enrollment_view', name="change_enrollment"),

        #About the course
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/about$',
            'courseware.views.course_about', name="about_course"),

        #Inside the course
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/$',
            'courseware.views.course_info', name="course_root"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/info$',
            'courseware.views.course_info', name="info"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/syllabus$',
            'courseware.views.syllabus', name="syllabus"), # TODO arjun remove when custom tabs in place, see courseware/courses.py
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/book/(?P<book_index>[^/]*)/$',
            'staticbook.views.index', name="book"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/book/(?P<book_index>[^/]*)/(?P<page>[^/]*)$',
            'staticbook.views.index'),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/book-shifted/(?P<page>[^/]*)$',
            'staticbook.views.index_shifted'),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/courseware/?$',
            'courseware.views.index', name="courseware"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/courseware/(?P<chapter>[^/]*)/$',
            'courseware.views.index', name="courseware_chapter"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$',
            'courseware.views.index', name="courseware_section"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/(?P<position>[^/]*)/?$',
            'courseware.views.index', name="courseware_position"),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/progress$',
            'courseware.views.progress', name="progress"),
        # Takes optional student_id for instructor use--shows profile as that student sees it.
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/progress/(?P<student_id>[^/]*)/$',
            'courseware.views.progress', name="student_progress"),

        # For the instructor
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/instructor$',
            'instructor.views.instructor_dashboard', name="instructor_dashboard"),

        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/gradebook$',
            'instructor.views.gradebook', name='gradebook'),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/grade_summary$',
            'instructor.views.grade_summary', name='grade_summary'),
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/enroll_students$',
            'instructor.views.enroll_students', name='enroll_students'),
    )

    # discussion forums live within courseware, so courseware must be enabled first
    if settings.MITX_FEATURES.get('ENABLE_DISCUSSION_SERVICE'):

        urlpatterns += (
            url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/news$',
                'courseware.views.news', name="news"),
            url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/discussion/',
                include('django_comment_client.urls'))
            )
    urlpatterns += (
        # This MUST be the last view in the courseware--it's a catch-all for custom tabs.
        url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/(?P<tab_slug>[^/]+)/$',
        'courseware.views.static_tab', name="static_tab"),
        )

if settings.QUICKEDIT:
    urlpatterns += (url(r'^quickedit/(?P<id>[^/]*)$', 'dogfood.views.quickedit'),)
    urlpatterns += (url(r'^dogfood/(?P<id>[^/]*)$', 'dogfood.views.df_capa_problem'),)

if settings.ASKBOT_ENABLED:
    urlpatterns += (url(r'^%s' % settings.ASKBOT_URL, include('askbot.urls')), \
                    url(r'^settings/', include('askbot.deps.livesettings.urls')), \
                    url(r'^followit/', include('followit.urls')), \
#                       url(r'^robots.txt$', include('robots.urls')),
                              )



if settings.DEBUG:
    ## Jasmine and admin
    urlpatterns=urlpatterns + (url(r'^_jasmine/', include('django_jasmine.urls')),
                    url(r'^admin/', include(admin.site.urls)),
                    )

if settings.MITX_FEATURES.get('AUTH_USE_OPENID'):
    urlpatterns += (
        url(r'^openid/login/$', 'django_openid_auth.views.login_begin', name='openid-login'),
        url(r'^openid/complete/$', 'external_auth.views.openid_login_complete', name='openid-complete'),
        url(r'^openid/logo.gif$', 'django_openid_auth.views.logo', name='openid-logo'),
    )

if settings.MITX_FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
    urlpatterns += (
        url(r'^openid/provider/login/$', 'external_auth.views.provider_login', name='openid-provider-login'),
        url(r'^openid/provider/login/(?:[\w%\. ]+)$', 'external_auth.views.provider_identity', name='openid-provider-login-identity'),
        url(r'^openid/provider/identity/$', 'external_auth.views.provider_identity', name='openid-provider-identity'),
        url(r'^openid/provider/xrds/$', 'external_auth.views.provider_xrds', name='openid-provider-xrds')
    )

if settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'):
    urlpatterns += (
        url(r'^migrate/modules$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^migrate/reload/(?P<reload_dir>[^/]+)$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^migrate/reload/(?P<reload_dir>[^/]+)/(?P<commit_id>[^/]+)$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^gitreload$', 'lms_migration.migrate.gitreload'),
        url(r'^gitreload/(?P<reload_dir>[^/]+)$', 'lms_migration.migrate.gitreload'),
        )

if settings.MITX_FEATURES.get('ENABLE_SQL_TRACKING_LOGS'):
    urlpatterns += (
        url(r'^event_logs$', 'track.views.view_tracking_log'),
        url(r'^event_logs/(?P<args>.+)$', 'track.views.view_tracking_log'),
        )

urlpatterns = patterns(*urlpatterns)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

#Custom error pages
handler404 = 'static_template_view.views.render_404'
handler500 = 'static_template_view.views.render_500'
