from django.conf import settings
from django.conf.urls import patterns, include, url
from ratelimitbackend import admin
from django.conf.urls.static import static

import django.contrib.auth.views
from microsite_configuration import microsite

# Uncomment the next two lines to enable the admin:
if settings.DEBUG or settings.FEATURES.get('ENABLE_DJANGO_ADMIN_SITE'):
    admin.autodiscover()

urlpatterns = ('',  # nopep8
    # certificate view
    url(r'^update_certificate$', 'certificates.views.update_certificate'),
    url(r'^request_certificate$', 'certificates.views.request_certificate'),
    url(r'^$', 'branding.views.index', name="root"),   # Main marketing page, or redirect to courseware
    url(r'^dashboard$', 'student.views.dashboard', name="dashboard"),
    url(r'^login$', 'student.views.signin_user', name="signin_user"),
    url(r'^register$', 'student.views.register_user', name="register_user"),

    url(r'^admin_dashboard$', 'dashboard.views.dashboard'),

    url(r'^change_email$', 'student.views.change_email_request', name="change_email"),
    url(r'^email_confirm/(?P<key>[^/]*)$', 'student.views.confirm_email_change'),
    url(r'^change_name$', 'student.views.change_name_request', name="change_name"),
    url(r'^accept_name_change$', 'student.views.accept_name_change'),
    url(r'^reject_name_change$', 'student.views.reject_name_change'),
    url(r'^pending_name_changes$', 'student.views.pending_name_changes'),
    url(r'^event$', 'track.views.user_track'),
    url(r'^segmentio/event$', 'track.views.segmentio.track_segmentio_event'),
    url(r'^t/(?P<template>[^/]*)$', 'static_template_view.views.index'),   # TODO: Is this used anymore? What is STATIC_GRAB?

    url(r'^accounts/login$', 'student.views.accounts_login', name="accounts_login"),
    url(r'^accounts/manage_user_standing', 'student.views.manage_user_standing',
        name='manage_user_standing'),
    url(r'^accounts/disable_account_ajax$', 'student.views.disable_account_ajax',
        name="disable_account_ajax"),

    url(r'^login_ajax$', 'student.views.login_user', name="login"),
    url(r'^login_ajax/(?P<error>[^/]*)$', 'student.views.login_user'),
    url(r'^logout$', 'student.views.logout_user', name='logout'),
    url(r'^create_account$', 'student.views.create_account', name='create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account', name="activate"),

    url(r'^password_reset/$', 'student.views.password_reset', name='password_reset'),
    ## Obsolete Django views for password resets
    ## TODO: Replace with Mako-ized views
    url(r'^password_change/$', django.contrib.auth.views.password_change,
        name='auth_password_change'),
    url(r'^password_change_done/$', django.contrib.auth.views.password_change_done,
        name='auth_password_change_done'),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'student.views.password_reset_confirm_wrapper',
        name='auth_password_reset_confirm'),
    url(r'^password_reset_complete/$', django.contrib.auth.views.password_reset_complete,
        name='auth_password_reset_complete'),
    url(r'^password_reset_done/$', django.contrib.auth.views.password_reset_done,
        name='auth_password_reset_done'),

    url(r'^heartbeat$', include('heartbeat.urls')),

    url(r'^user_api/', include('user_api.urls')),

    url(r'^notifier_api/', include('notifier_api.urls')),

    url(r'^lang_pref/', include('lang_pref.urls')),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^embargo$', 'student.views.embargo', name="embargo"),

    # Feedback Form endpoint
    url(r'^submit_feedback$', 'util.views.submit_feedback'),

)

if settings.FEATURES["ENABLE_MOBILE_REST_API"]:
    urlpatterns += (
        url(r'^api/mobile/v0.5/', include('mobile_api.urls')),
        # Video Abstraction Layer used to allow video teams to manage video assets
        # independently of courseware. https://github.com/edx/edx-val
        url(r'^api/val/v0/', include('edxval.urls')),
    )

# if settings.FEATURES.get("MULTIPLE_ENROLLMENT_ROLES"):
urlpatterns += (
    url(r'^verify_student/', include('verify_student.urls')),
    url(r'^course_modes/', include('course_modes.urls')),
)


js_info_dict = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

urlpatterns += (
    # Serve catalog of localized strings to be rendered by Javascript
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
)

# sysadmin dashboard, to see what courses are loaded, to delete & load courses
if settings.FEATURES["ENABLE_SYSADMIN_DASHBOARD"]:
    urlpatterns += (
        url(r'^sysadmin/', include('dashboard.sysadmin_urls')),
    )

urlpatterns += (
    url(r'^support/', include('dashboard.support_urls')),
)

#Semi-static views (these need to be rendered and have the login bar, but don't change)
urlpatterns += (
    url(r'^404$', 'static_template_view.views.render',
        {'template': '404.html'}, name="404"),
)

# Favicon
favicon_path = microsite.get_value('favicon_path', settings.FAVICON_PATH)
urlpatterns += ((
    r'^favicon\.ico$',
    'django.views.generic.simple.redirect_to',
    {'url':  settings.STATIC_URL + favicon_path}
),)

# Semi-static views only used by edX, not by themes
if not settings.FEATURES["USE_CUSTOM_THEME"]:
    urlpatterns += (
        url(r'^blog$', 'static_template_view.views.render',
            {'template': 'blog.html'}, name="blog"),
        url(r'^contact$', 'static_template_view.views.render',
            {'template': 'contact.html'}, name="contact"),
        url(r'^donate$', 'static_template_view.views.render',
            {'template': 'donate.html'}, name="donate"),
        url(r'^faq$', 'static_template_view.views.render',
            {'template': 'faq.html'}, name="faq"),
        url(r'^help$', 'static_template_view.views.render',
            {'template': 'help.html'}, name="help_edx"),
        url(r'^jobs$', 'static_template_view.views.render',
            {'template': 'jobs.html'}, name="jobs"),
        url(r'^news$', 'static_template_view.views.render',
            {'template': 'news.html'}, name="news"),
        url(r'^press$', 'static_template_view.views.render',
            {'template': 'press.html'}, name="press"),
        url(r'^media-kit$', 'static_template_view.views.render',
            {'template': 'media-kit.html'}, name="media-kit"),

        # TODO: (bridger) The copyright has been removed until it is updated for edX
        # url(r'^copyright$', 'static_template_view.views.render',
        #     {'template': 'copyright.html'}, name="copyright"),

        # Press releases
        url(r'^press/([_a-zA-Z0-9-]+)$', 'static_template_view.views.render_press_release', name='press_release'),
)

# Only enable URLs for those marketing links actually enabled in the
# settings. Disable URLs by marking them as None.
for key, value in settings.MKTG_URL_LINK_MAP.items():
    # Skip disabled URLs
    if value is None:
        continue

    # These urls are enabled separately
    if key == "ROOT" or key == "COURSES":
        continue

    # Make the assumptions that the templates are all in the same dir
    # and that they all match the name of the key (plus extension)
    template = "%s.html" % key.lower()

    # To allow theme templates to inherit from default templates,
    # prepend a standard prefix
    if settings.FEATURES["USE_CUSTOM_THEME"]:
        template = "theme-" + template

    # Make the assumption that the URL we want is the lowercased
    # version of the map key
    urlpatterns += (url(r'^%s$' % key.lower(),
                        'static_template_view.views.render',
                        {'template': template}, name=value),)


# Multicourse wiki (Note: wiki urls must be above the courseware ones because of
# the custom tab catch-all)
if settings.WIKI_ENABLED:
    from wiki.urls import get_pattern as wiki_pattern
    from django_notify.urls import get_pattern as notify_pattern

    urlpatterns += (
        # First we include views from course_wiki that we use to override the default views.
        # They come first in the urlpatterns so they get resolved first
        url('^wiki/create-root/$', 'course_wiki.views.root_create', name='root_create'),
        url(r'^wiki/', include(wiki_pattern())),
        url(r'^notify/', include(notify_pattern())),

        # These urls are for viewing the wiki in the context of a course. They should
        # never be returned by a reverse() so they come after the other url patterns
        url(r'^courses/{}/course_wiki/?$'.format(settings.COURSE_ID_PATTERN),
            'course_wiki.views.course_wiki_redirect', name="course_wiki"),
        url(r'^courses/{}/wiki/'.format(settings.COURSE_KEY_REGEX), include(wiki_pattern())),
    )

if settings.COURSEWARE_ENABLED:
    urlpatterns += (
        url(r'^courses/{}/jump_to/(?P<location>.*)$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.jump_to', name="jump_to"),
        url(r'^courses/{}/jump_to_id/(?P<module_id>.*)$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.jump_to_id', name="jump_to_id"),
        url(r'^courses/{course_key}/xblock/{usage_key}/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(course_key=settings.COURSE_ID_PATTERN, usage_key=settings.USAGE_ID_PATTERN),
            'courseware.module_render.handle_xblock_callback',
            name='xblock_handler'),
        url(r'^courses/{course_key}/xblock/{usage_key}/handler_noauth/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(course_key=settings.COURSE_ID_PATTERN, usage_key=settings.USAGE_ID_PATTERN),
            'courseware.module_render.handle_xblock_callback_noauth',
            name='xblock_handler_noauth'),
        url(r'xblock/resource/(?P<block_type>[^/]+)/(?P<uri>.*)$',
            'courseware.module_render.xblock_resource',
            name='xblock_resource_url'),

        # Software Licenses

        # TODO: for now, this is the endpoint of an ajax replay
        # service that retrieve and assigns license numbers for
        # software assigned to a course. The numbers have to be loaded
        # into the database.
        url(r'^software-licenses$', 'licenses.views.user_software_license', name="user_software_license"),

        url(r'^courses/{}/xqueue/(?P<userid>[^/]*)/(?P<mod_id>.*?)/(?P<dispatch>[^/]*)$'.format(settings.COURSE_ID_PATTERN),
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
            'student.views.change_enrollment', name="change_enrollment"),
        url(r'^change_email_settings$', 'student.views.change_email_settings', name="change_email_settings"),

        #About the course
        url(r'^courses/{}/about$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.course_about', name="about_course"),
        #View for mktg site (kept for backwards compatibility TODO - remove before merge to master)
        url(r'^courses/{}/mktg-about$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.mktg_course_about', name="mktg_about_course"),
        #View for mktg site
        url(r'^mktg/{}/?$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.mktg_course_about', name="mktg_about_course"),

        #Inside the course
        url(r'^courses/{}/$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.course_info', name="course_root"),
        url(r'^courses/{}/info$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.course_info', name="info"),
        url(r'^courses/{}/syllabus$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.syllabus', name="syllabus"),   # TODO arjun remove when custom tabs in place, see courseware/courses.py

        url(r'^courses/{}/book/(?P<book_index>\d+)/$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.index', name="book"),
        url(r'^courses/{}/book/(?P<book_index>\d+)/(?P<page>\d+)$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.index', name="book"),

        url(r'^courses/{}/pdfbook/(?P<book_index>\d+)/$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.pdf_index', name="pdf_book"),
        url(r'^courses/{}/pdfbook/(?P<book_index>\d+)/(?P<page>\d+)$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.pdf_index', name="pdf_book"),

        url(r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.pdf_index', name="pdf_book"),
        url(r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/(?P<page>\d+)$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.pdf_index', name="pdf_book"),

        url(r'^courses/{}/htmlbook/(?P<book_index>\d+)/$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.html_index', name="html_book"),
        url(r'^courses/{}/htmlbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(settings.COURSE_ID_PATTERN),
            'staticbook.views.html_index', name="html_book"),

        url(r'^courses/{}/courseware/?$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.index', name="courseware"),
        url(r'^courses/{}/courseware/(?P<chapter>[^/]*)/$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.index', name="courseware_chapter"),
        url(r'^courses/{}/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.index', name="courseware_section"),
        url(r'^courses/{}/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/(?P<position>[^/]*)/?$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.index', name="courseware_position"),

        url(r'^courses/{}/progress$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.progress', name="progress"),
        # Takes optional student_id for instructor use--shows profile as that student sees it.
        url(r'^courses/{}/progress/(?P<student_id>[^/]*)/$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.progress', name="student_progress"),

        # For the instructor
        url(r'^courses/{}/instructor$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.instructor_dashboard.instructor_dashboard_2', name="instructor_dashboard"),
        url(r'^courses/{}/set_course_mode_price$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.instructor_dashboard.set_course_mode_price', name="set_course_mode_price"),
        url(r'^courses/{}/instructor/api/'.format(settings.COURSE_ID_PATTERN),
            include('instructor.views.api_urls')),
        url(r'^courses/{}/remove_coupon$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.coupons.remove_coupon', name="remove_coupon"),
        url(r'^courses/{}/add_coupon$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.coupons.add_coupon', name="add_coupon"),
        url(r'^courses/{}/update_coupon$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.coupons.update_coupon', name="update_coupon"),
        url(r'^courses/{}/get_coupon_info$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.coupons.get_coupon_info', name="get_coupon_info"),

        # see ENABLE_INSTRUCTOR_LEGACY_DASHBOARD section for legacy dash urls

        # Open Ended grading views
        url(r'^courses/{}/staff_grading$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.staff_grading', name='staff_grading'),
        url(r'^courses/{}/staff_grading/get_next$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.staff_grading_service.get_next', name='staff_grading_get_next'),
        url(r'^courses/{}/staff_grading/save_grade$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.staff_grading_service.save_grade', name='staff_grading_save_grade'),
        url(r'^courses/{}/staff_grading/get_problem_list$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.staff_grading_service.get_problem_list', name='staff_grading_get_problem_list'),

        # Open Ended problem list
        url(r'^courses/{}/open_ended_problems$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.student_problem_list', name='open_ended_problems'),

        # Open Ended flagged problem list
        url(r'^courses/{}/open_ended_flagged_problems$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.flagged_problem_list', name='open_ended_flagged_problems'),
        url(r'^courses/{}/open_ended_flagged_problems/take_action_on_flags$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.take_action_on_flags', name='open_ended_flagged_problems_take_action'),

        # Cohorts management
        url(r'^courses/{}/cohorts$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.list_cohorts', name="cohorts"),
        url(r'^courses/{}/cohorts/add$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.add_cohort',
            name="add_cohort"),
        url(r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.users_in_cohort',
            name="list_cohort"),
        url(r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/add$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.add_users_to_cohort',
            name="add_to_cohort"),
        url(r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/delete$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.remove_user_from_cohort',
            name="remove_from_cohort"),
        url(r'^courses/{}/cohorts/debug$'.format(settings.COURSE_KEY_PATTERN),
            'course_groups.views.debug_cohort_mgmt',
            name="debug_cohort_mgmt"),

        # Open Ended Notifications
        url(r'^courses/{}/open_ended_notifications$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.combined_notifications', name='open_ended_notifications'),

        url(r'^courses/{}/peer_grading$'.format(settings.COURSE_ID_PATTERN),
            'open_ended_grading.views.peer_grading', name='peer_grading'),

        url(r'^courses/{}/notes$'.format(settings.COURSE_ID_PATTERN), 'notes.views.notes', name='notes'),
        url(r'^courses/{}/notes/'.format(settings.COURSE_ID_PATTERN), include('notes.urls')),

        # LTI endpoints listing
        url(r'^courses/{}/lti_rest_endpoints/'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.get_course_lti_endpoints', name='lti_rest_endpoints'),
    )

    # allow course staff to change to student view of courseware
    if settings.FEATURES.get('ENABLE_MASQUERADE'):
        urlpatterns += (
            url(r'^masquerade/(?P<marg>.*)$', 'courseware.masquerade.handle_ajax', name="masquerade-switch"),
        )

    # discussion forums live within courseware, so courseware must be enabled first
    if settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
        urlpatterns += (
            url(r'^courses/{}/discussion/'.format(settings.COURSE_ID_PATTERN),
                include('django_comment_client.urls')),
            url(r'^notification_prefs/enable/', 'notification_prefs.views.ajax_enable'),
            url(r'^notification_prefs/disable/', 'notification_prefs.views.ajax_disable'),
            url(r'^notification_prefs/status/', 'notification_prefs.views.ajax_status'),
            url(r'^notification_prefs/unsubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
                'notification_prefs.views.set_subscription', {'subscribe': False}, name="unsubscribe_forum_update"),
            url(r'^notification_prefs/resubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
                'notification_prefs.views.set_subscription', {'subscribe': True}, name="resubscribe_forum_update"),
        )
    urlpatterns += (
        # This MUST be the last view in the courseware--it's a catch-all for custom tabs.
        url(r'^courses/{}/(?P<tab_slug>[^/]+)/$'.format(settings.COURSE_ID_PATTERN),
            'courseware.views.static_tab', name="static_tab"),
    )

    if settings.FEATURES.get('ENABLE_STUDENT_HISTORY_VIEW'):
        urlpatterns += (
            url(r'^courses/{}/submission_history/(?P<student_username>[^/]*)/(?P<location>.*?)$'.format(settings.COURSE_ID_PATTERN),
                'courseware.views.submission_history',
                name='submission_history'),
        )


if settings.COURSEWARE_ENABLED and settings.FEATURES.get('ENABLE_INSTRUCTOR_LEGACY_DASHBOARD'):
    urlpatterns += (
        url(r'^courses/{}/legacy_instructor_dash$'.format(settings.COURSE_ID_PATTERN),
            'instructor.views.legacy.instructor_dashboard', name="instructor_dashboard_legacy"),
    )

if settings.FEATURES.get('CLASS_DASHBOARD'):
    urlpatterns += (
        url(r'^class_dashboard/', include('class_dashboard.urls')),
    )

if settings.DEBUG or settings.FEATURES.get('ENABLE_DJANGO_ADMIN_SITE'):
    ## Jasmine and admin
    urlpatterns += (url(r'^admin/', include(admin.site.urls)),)

if settings.FEATURES.get('AUTH_USE_OPENID'):
    urlpatterns += (
        url(r'^openid/login/$', 'django_openid_auth.views.login_begin', name='openid-login'),
        url(r'^openid/complete/$', 'external_auth.views.openid_login_complete', name='openid-complete'),
        url(r'^openid/logo.gif$', 'django_openid_auth.views.logo', name='openid-logo'),
    )

if settings.FEATURES.get('AUTH_USE_SHIB'):
    urlpatterns += (
        url(r'^shib-login/$', 'external_auth.views.shib_login', name='shib-login'),
    )

if settings.FEATURES.get('AUTH_USE_CAS'):
    urlpatterns += (
        url(r'^cas-auth/login/$', 'external_auth.views.cas_login', name="cas-login"),
        url(r'^cas-auth/logout/$', 'django_cas.views.logout', {'next_page': '/'}, name="cas-logout"),
    )

if settings.FEATURES.get('RESTRICT_ENROLL_BY_REG_METHOD'):
    urlpatterns += (
        url(r'^course_specific_login/{}/$'.format(settings.COURSE_ID_PATTERN),
            'external_auth.views.course_specific_login', name='course-specific-login'),
        url(r'^course_specific_register/{}/$'.format(settings.COURSE_ID_PATTERN),
            'external_auth.views.course_specific_register', name='course-specific-register'),

    )

# Shopping cart
urlpatterns += (
    url(r'^shoppingcart/', include('shoppingcart.urls')),
)


if settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
    urlpatterns += (
        url(r'^openid/provider/login/$', 'external_auth.views.provider_login', name='openid-provider-login'),
        url(r'^openid/provider/login/(?:.+)$', 'external_auth.views.provider_identity', name='openid-provider-login-identity'),
        url(r'^openid/provider/identity/$', 'external_auth.views.provider_identity', name='openid-provider-identity'),
        url(r'^openid/provider/xrds/$', 'external_auth.views.provider_xrds', name='openid-provider-xrds')
    )

if settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    urlpatterns += (
        url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2')),
    )


if settings.FEATURES.get('ENABLE_LMS_MIGRATION'):
    urlpatterns += (
        url(r'^migrate/modules$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^migrate/reload/(?P<reload_dir>[^/]+)$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^migrate/reload/(?P<reload_dir>[^/]+)/(?P<commit_id>[^/]+)$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^gitreload$', 'lms_migration.migrate.gitreload'),
        url(r'^gitreload/(?P<reload_dir>[^/]+)$', 'lms_migration.migrate.gitreload'),
    )

if settings.FEATURES.get('ENABLE_SQL_TRACKING_LOGS'):
    urlpatterns += (
        url(r'^event_logs$', 'track.views.view_tracking_log'),
        url(r'^event_logs/(?P<args>.+)$', 'track.views.view_tracking_log'),
    )

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += (
        url(r'^status/', include('service_status.urls')),
    )

if settings.FEATURES.get('ENABLE_INSTRUCTOR_BACKGROUND_TASKS'):
    urlpatterns += (
        url(r'^instructor_task_status/$', 'instructor_task.views.instructor_task_status', name='instructor_task_status'),
    )

if settings.FEATURES.get('RUN_AS_ANALYTICS_SERVER_ENABLED'):
    urlpatterns += (
        url(r'^edinsights_service/', include('edinsights.core.urls')),
    )
    import edinsights.core.registry

# FoldIt views
urlpatterns += (
    # The path is hardcoded into their app...
    url(r'^comm/foldit_ops', 'foldit.views.foldit_ops', name="foldit_ops"),
)

if settings.FEATURES.get('ENABLE_DEBUG_RUN_PYTHON'):
    urlpatterns += (
        url(r'^debug/run_python$', 'debug.views.run_python'),
    )

urlpatterns += (
    url(r'^debug/show_parameters$', 'debug.views.show_parameters'),
)

# Crowdsourced hinting instructor manager.
if settings.FEATURES.get('ENABLE_HINTER_INSTRUCTOR_VIEW'):
    urlpatterns += (
        url(r'^courses/{}/hint_manager$'.format(settings.COURSE_ID_PATTERN),
            'instructor.hint_manager.hint_manager', name="hint_manager"),
    )

# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += (
        url(r'^auto_auth$', 'student.views.auto_auth'),
    )

# Third-party auth.
if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    urlpatterns += (
        url(r'', include('third_party_auth.urls')),
    )

# If enabled, expose the URLs for the new dashboard, account, and profile pages
if settings.FEATURES.get('ENABLE_NEW_DASHBOARD'):
    urlpatterns += (
        url(r'^profile/', include('student_profile.urls')),
        url(r'^account/', include('student_account.urls')),
    )

urlpatterns = patterns(*urlpatterns)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # in debug mode, allow any template to be rendered (most useful for UX reference templates)
    urlpatterns += url(r'^template/(?P<template>.+)$', 'debug.views.show_reference_template'),

#Custom error pages
handler404 = 'static_template_view.views.render_404'
handler500 = 'static_template_view.views.render_500'

# display error page templates, for testing purposes
urlpatterns += (
    url(r'404', handler404),
    url(r'500', handler500),
)
