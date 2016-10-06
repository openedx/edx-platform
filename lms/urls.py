"""
URLs for LMS
"""

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from ratelimitbackend import admin
from django.conf.urls.static import static

from courseware.views.views import EnrollStaffView
from config_models.views import ConfigurationModelCurrentAPIView
from courseware.views.index import CoursewareIndex
from openedx.core.djangoapps.auth_exchange.views import LoginWithAccessTokenView
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# Uncomment the next two lines to enable the admin:
if settings.DEBUG or settings.FEATURES.get('ENABLE_DJANGO_ADMIN_SITE'):
    admin.autodiscover()

# Use urlpatterns formatted as within the Django docs with first parameter "stuck" to the open parenthesis
urlpatterns = (
    '',

    url(r'^$', 'branding.views.index', name="root"),   # Main marketing page, or redirect to courseware

    url(r'', include('student.urls')),
    # TODO: Move lms specific student views out of common code
    url(r'^dashboard$', 'student.views.dashboard', name="dashboard"),
    url(r'^change_enrollment$', 'student.views.change_enrollment', name='change_enrollment'),

    # Event tracking endpoints
    url(r'', include('track.urls')),

    # Performance endpoints
    url(r'', include('openedx.core.djangoapps.performance.urls')),

    # Static template view endpoints like blog, faq, etc.
    url(r'', include('static_template_view.urls')),

    url(r'^heartbeat$', include('openedx.core.djangoapps.heartbeat.urls')),

    # Note: these are older versions of the User API that will eventually be
    # subsumed by api/user listed below.
    url(r'^user_api/', include('openedx.core.djangoapps.user_api.legacy_urls')),

    url(r'^notifier_api/', include('notifier_api.urls')),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    # Feedback Form endpoint
    url(r'^submit_feedback$', 'util.views.submit_feedback'),

    # Enrollment API RESTful endpoints
    url(r'^api/enrollment/v1/', include('enrollment.urls')),

    # Courseware search endpoints
    url(r'^search/', include('search.urls')),

    # Course content API
    url(r'^api/course_structure/', include('course_structure_api.urls', namespace='course_structure_api')),

    # Course API
    url(r'^api/courses/', include('course_api.urls')),

    # User API endpoints
    url(r'^api/user/', include('openedx.core.djangoapps.user_api.urls')),

    # Bookmarks API endpoints
    url(r'^api/bookmarks/', include('openedx.core.djangoapps.bookmarks.urls')),

    # Profile Images API endpoints
    url(r'^api/profile_images/', include('openedx.core.djangoapps.profile_images.urls')),

    # Video Abstraction Layer used to allow video teams to manage video assets
    # independently of courseware. https://github.com/edx/edx-val
    url(r'^api/val/v0/', include('edxval.urls')),

    url(r'^api/commerce/', include('commerce.api.urls', namespace='commerce_api')),
    url(r'^api/credit/', include('openedx.core.djangoapps.credit.urls', app_name="credit", namespace='credit')),
    url(r'^rss_proxy/', include('rss_proxy.urls', namespace='rss_proxy')),
    url(r'^api/organizations/', include('organizations.urls', namespace='organizations')),

    # Update session view
    url(r'^lang_pref/session_language', 'lang_pref.views.update_session_language', name='session_language'),

    # Multiple course modes and identity verification
    # TODO Namespace these!
    url(r'^course_modes/', include('course_modes.urls')),
    url(r'^verify_student/', include('verify_student.urls')),

    url(r'^update_lang/', include('dark_lang.urls', namespace='darklang')),
    # URLs for API access management
    url(r'^api-admin/', include('openedx.core.djangoapps.api_admin.urls', namespace='api_admin')),
)

urlpatterns += (
    url(r'^dashboard/', include('learner_dashboard.urls')),
)

# TODO: This needs to move to a separate urls.py once the student_account and
# student views below find a home together
if settings.FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"]:
    # Backwards compatibility with old URL structure, but serve the new views
    urlpatterns += (
        url(r'^login$', 'student_account.views.login_and_registration_form',
            {'initial_mode': 'login'}, name="signin_user"),
        url(r'^register$', 'student_account.views.login_and_registration_form',
            {'initial_mode': 'register'}, name="register_user"),
    )
else:
    # Serve the old views
    urlpatterns += (
        url(r'^login$', 'student.views.signin_user', name="signin_user"),
        url(r'^register$', 'student.views.register_user', name="register_user"),
    )

if settings.FEATURES["ENABLE_MOBILE_REST_API"]:
    urlpatterns += (
        url(r'^api/mobile/v0.5/', include('mobile_api.urls')),
    )

if settings.FEATURES["ENABLE_OPENBADGES"]:
    urlpatterns += (
        url(r'^api/badges/v1/', include('badges.api.urls', app_name="badges", namespace="badges_api")),
    )

js_info_dict = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

# sysadmin dashboard, to see what courses are loaded, to delete & load courses
if settings.FEATURES["ENABLE_SYSADMIN_DASHBOARD"]:
    urlpatterns += (
        url(r'^sysadmin/', include('dashboard.sysadmin_urls')),
    )

urlpatterns += (
    url(r'^support/', include('support.urls', app_name="support", namespace='support')),
)

# Favicon
favicon_path = configuration_helpers.get_value('favicon_path', settings.FAVICON_PATH)  # pylint: disable=invalid-name
urlpatterns += (url(
    r'^favicon\.ico$',
    RedirectView.as_view(url=settings.STATIC_URL + favicon_path, permanent=True)
),)

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

COURSE_URLS = patterns(
    '',
    url(
        r'^look_up_registration_code$',
        'lms.djangoapps.instructor.views.registration_codes.look_up_registration_code',
        name='look_up_registration_code',
    ),
    url(
        r'^registration_code_details$',
        'lms.djangoapps.instructor.views.registration_codes.registration_code_details',
        name='registration_code_details',
    ),
)
urlpatterns += (
    # jump_to URLs for direct access to a location in the course
    url(
        r'^courses/{}/jump_to/(?P<location>.*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.jump_to',
        name='jump_to',
    ),
    url(
        r'^courses/{}/jump_to_id/(?P<module_id>.*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.jump_to_id',
        name='jump_to_id',
    ),

    # xblock Handler APIs
    url(
        r'^courses/{course_key}/xblock/{usage_key}/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(
            course_key=settings.COURSE_ID_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN,
        ),
        'courseware.module_render.handle_xblock_callback',
        name='xblock_handler',
    ),
    url(
        r'^courses/{course_key}/xblock/{usage_key}/handler_noauth/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(
            course_key=settings.COURSE_ID_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN,
        ),
        'courseware.module_render.handle_xblock_callback_noauth',
        name='xblock_handler_noauth',
    ),

    # xblock View API
    # (unpublished) API that returns JSON with the HTML fragment and related resources
    # for the xBlock's requested view.
    url(
        r'^courses/{course_key}/xblock/{usage_key}/view/(?P<view_name>[^/]*)$'.format(
            course_key=settings.COURSE_ID_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN,
        ),
        'courseware.module_render.xblock_view',
        name='xblock_view',
    ),

    # xblock Rendering View URL
    # URL to provide an HTML view of an xBlock. The view type (e.g., student_view) is
    # passed as a "view" parameter to the URL.
    # Note: This is not an API. Compare this with the xblock_view API above.
    url(
        r'^xblock/{usage_key_string}$'.format(usage_key_string=settings.USAGE_KEY_PATTERN),
        'courseware.views.views.render_xblock',
        name='render_xblock',
    ),

    # xblock Resource URL
    url(
        r'xblock/resource/(?P<block_type>[^/]+)/(?P<uri>.*)$',
        'openedx.core.djangoapps.common_views.xblock.xblock_resource',
        name='xblock_resource_url',
    ),

    url(
        r'^courses/{}/xqueue/(?P<userid>[^/]*)/(?P<mod_id>.*?)/(?P<dispatch>[^/]*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.module_render.xqueue_callback',
        name='xqueue_callback',
    ),

    # TODO: These views need to be updated before they work
    url(r'^calculate$', 'util.views.calculate'),

    url(r'^courses/?$', 'branding.views.courses', name="courses"),

    #About the course
    url(
        r'^courses/{}/about$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.course_about',
        name='about_course',
    ),

    url(
        r'^courses/{}/enroll_staff$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        EnrollStaffView.as_view(),
        name='enroll_staff',
    ),

    #Inside the course
    url(
        r'^courses/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.course_info',
        name='course_root',
    ),
    url(
        r'^courses/{}/info$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.course_info',
        name='info',
    ),
    # TODO arjun remove when custom tabs in place, see courseware/courses.py
    url(
        r'^courses/{}/syllabus$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.syllabus',
        name='syllabus',
    ),

    # Survey associated with a course
    url(
        r'^courses/{}/survey$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.course_survey',
        name='course_survey',
    ),

    url(
        r'^courses/{}/book/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.index',
        name='book',
    ),
    url(
        r'^courses/{}/book/(?P<book_index>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.index',
        name='book',
    ),

    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.pdf_index',
        name='pdf_book',
    ),
    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.pdf_index',
        name='pdf_book',
    ),

    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.pdf_index',
        name='pdf_book',
    ),
    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.pdf_index',
        name='pdf_book',
    ),

    url(
        r'^courses/{}/htmlbook/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.html_index',
        name='html_book',
    ),
    url(
        r'^courses/{}/htmlbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'staticbook.views.html_index',
        name='html_book',
    ),

    url(
        r'^courses/{}/courseware/?$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CoursewareIndex.as_view(),
        name='courseware',
    ),
    url(
        r'^courses/{}/courseware/(?P<chapter>[^/]*)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CoursewareIndex.as_view(),
        name='courseware_chapter',
    ),
    url(
        r'^courses/{}/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CoursewareIndex.as_view(),
        name='courseware_section',
    ),
    url(
        r'^courses/{}/courseware/(?P<chapter>[^/]*)/(?P<section>[^/]*)/(?P<position>[^/]*)/?$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CoursewareIndex.as_view(),
        name='courseware_position',
    ),

    # progress page
    url(
        r'^courses/{}/progress$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.progress',
        name='progress',
    ),

    # Takes optional student_id for instructor use--shows profile as that student sees it.
    url(
        r'^courses/{}/progress/(?P<student_id>[^/]*)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.progress',
        name='student_progress',
    ),

    # rest api for grades
    url(
        r'^api/grades/',
        include('lms.djangoapps.grades.api.urls', namespace='grades_api')
    ),


    # For the instructor
    url(
        r'^courses/{}/instructor$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.instructor_dashboard.instructor_dashboard_2',
        name='instructor_dashboard',
    ),


    url(
        r'^courses/{}/set_course_mode_price$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.instructor_dashboard.set_course_mode_price',
        name='set_course_mode_price',
    ),
    url(
        r'^courses/{}/instructor/api/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('lms.djangoapps.instructor.views.api_urls')),
    url(
        r'^courses/{}/remove_coupon$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.coupons.remove_coupon',
        name='remove_coupon',
    ),
    url(
        r'^courses/{}/add_coupon$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.coupons.add_coupon',
        name='add_coupon',
    ),
    url(
        r'^courses/{}/update_coupon$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.coupons.update_coupon',
        name='update_coupon',
    ),
    url(
        r'^courses/{}/get_coupon_info$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'lms.djangoapps.instructor.views.coupons.get_coupon_info',
        name='get_coupon_info',
    ),

    url(
        r'^courses/{}/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include(COURSE_URLS)
    ),

    # Cohorts management
    url(
        r'^courses/{}/cohorts/settings$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.course_cohort_settings_handler',
        name='course_cohort_settings',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)?$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.cohort_handler',
        name='cohorts',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.users_in_cohort',
        name='list_cohort',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/add$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.add_users_to_cohort',
        name='add_to_cohort',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/delete$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.remove_user_from_cohort',
        name='remove_from_cohort',
    ),
    url(
        r'^courses/{}/cohorts/debug$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.debug_cohort_mgmt',
        name='debug_cohort_mgmt',
    ),
    url(
        r'^courses/{}/cohorts/topics$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'openedx.core.djangoapps.course_groups.views.cohort_discussion_topics',
        name='cohort_discussion_topics',
    ),
    url(
        r'^courses/{}/verified_track_content/settings'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'verified_track_content.views.cohorting_settings',
        name='verified_track_cohorting',
    ),
    url(
        r'^courses/{}/notes$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'notes.views.notes',
        name='notes',
    ),
    url(
        r'^courses/{}/notes/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('notes.urls')
    ),

    # LTI endpoints listing
    url(
        r'^courses/{}/lti_rest_endpoints/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.get_course_lti_endpoints',
        name='lti_rest_endpoints',
    ),

    # Student account
    url(
        r'^account/',
        include('student_account.urls')
    ),

    # Student profile
    url(
        r'^u/(?P<username>[\w.@+-]+)$',
        'student_profile.views.learner_profile',
        name='learner_profile',
    ),

    # Student Notes
    url(
        r'^courses/{}/edxnotes'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('edxnotes.urls'),
        name='edxnotes_endpoints',
    ),

    url(
        r'^api/branding/v1/',
        include('branding.api_urls')
    ),
)

if settings.FEATURES["ENABLE_TEAMS"]:
    # Teams endpoints
    urlpatterns += (
        url(
            r'^api/team/',
            include('lms.djangoapps.teams.api_urls')
        ),
        url(
            r'^courses/{}/teams'.format(
                settings.COURSE_ID_PATTERN,
            ),
            include('lms.djangoapps.teams.urls'),
            name='teams_endpoints',
        ),
    )

# allow course staff to change to student view of courseware
if settings.FEATURES.get('ENABLE_MASQUERADE'):
    urlpatterns += (
        url(
            r'^courses/{}/masquerade$'.format(
                settings.COURSE_KEY_PATTERN,
            ),
            'courseware.masquerade.handle_ajax',
            name='masquerade_update',
        ),
    )

urlpatterns += (
    url(
        r'^courses/{}/generate_user_cert'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.generate_user_cert',
        name='generate_user_cert',
    ),
)

# discussion forums live within courseware, so courseware must be enabled first
if settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
    urlpatterns += (
        url(
            r'^api/discussion/',
            include('discussion_api.urls')
        ),
        url(
            r'^courses/{}/discussion/'.format(
                settings.COURSE_ID_PATTERN,
            ),
            include('django_comment_client.urls')
        ),
        url(
            r'^courses/{}/discussion/forum/'.format(
                settings.COURSE_ID_PATTERN,
            ),
            include('discussion.urls')
        ),
        url(
            r'^notification_prefs/enable/',
            'notification_prefs.views.ajax_enable'
        ),
        url(
            r'^notification_prefs/disable/',
            'notification_prefs.views.ajax_disable'
        ),
        url(
            r'^notification_prefs/status/',
            'notification_prefs.views.ajax_status'
        ),
        url(
            r'^notification_prefs/unsubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
            'notification_prefs.views.set_subscription',
            {
                'subscribe': False,
            },
            name='unsubscribe_forum_update',
        ),
        url(
            r'^notification_prefs/resubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
            'notification_prefs.views.set_subscription',
            {
                'subscribe': True,
            },
            name='resubscribe_forum_update',
        ),
    )
urlpatterns += (
    # This MUST be the last view in the courseware--it's a catch-all for custom tabs.
    url(
        r'^courses/{}/(?P<tab_slug>[^/]+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        'courseware.views.views.static_tab',
        name='static_tab',
    ),
)

if settings.FEATURES.get('ENABLE_STUDENT_HISTORY_VIEW'):
    urlpatterns += (
        url(
            r'^courses/{}/submission_history/(?P<student_username>[^/]*)/(?P<location>.*?)$'.format(
                settings.COURSE_ID_PATTERN
            ),
            'courseware.views.views.submission_history',
            name='submission_history',
        ),
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
        url(
            r'^openid/complete/$',
            'openedx.core.djangoapps.external_auth.views.openid_login_complete',
            name='openid-complete',
        ),
        url(r'^openid/logo.gif$', 'django_openid_auth.views.logo', name='openid-logo'),
    )

if settings.FEATURES.get('AUTH_USE_SHIB'):
    urlpatterns += (
        url(r'^shib-login/$', 'openedx.core.djangoapps.external_auth.views.shib_login', name='shib-login'),
    )

if settings.FEATURES.get('AUTH_USE_CAS'):
    urlpatterns += (
        url(r'^cas-auth/login/$', 'openedx.core.djangoapps.external_auth.views.cas_login', name="cas-login"),
        url(r'^cas-auth/logout/$', 'django_cas.views.logout', {'next_page': '/'}, name="cas-logout"),
    )

if settings.FEATURES.get('RESTRICT_ENROLL_BY_REG_METHOD'):
    urlpatterns += (
        url(r'^course_specific_login/{}/$'.format(settings.COURSE_ID_PATTERN),
            'openedx.core.djangoapps.external_auth.views.course_specific_login', name='course-specific-login'),
        url(r'^course_specific_register/{}/$'.format(settings.COURSE_ID_PATTERN),
            'openedx.core.djangoapps.external_auth.views.course_specific_register', name='course-specific-register'),

    )

# Shopping cart
urlpatterns += (
    url(r'^shoppingcart/', include('shoppingcart.urls')),
    url(r'^commerce/', include('commerce.urls', namespace='commerce')),
)

# Embargo
if settings.FEATURES.get('EMBARGO'):
    urlpatterns += (
        url(r'^embargo/', include('embargo.urls')),
    )

# Survey Djangoapp
urlpatterns += (
    url(r'^survey/', include('survey.urls')),
)

if settings.FEATURES.get('AUTH_USE_OPENID_PROVIDER'):
    urlpatterns += (
        url(
            r'^openid/provider/login/$',
            'openedx.core.djangoapps.external_auth.views.provider_login',
            name='openid-provider-login',
        ),
        url(
            r'^openid/provider/login/(?:.+)$',
            'openedx.core.djangoapps.external_auth.views.provider_identity',
            name='openid-provider-login-identity'
        ),
        url(
            r'^openid/provider/identity/$',
            'openedx.core.djangoapps.external_auth.views.provider_identity',
            name='openid-provider-identity',
        ),
        url(
            r'^openid/provider/xrds/$',
            'openedx.core.djangoapps.external_auth.views.provider_xrds',
            name='openid-provider-xrds',
        ),
    )

if settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    urlpatterns += (
        # These URLs dispatch to django-oauth-toolkit or django-oauth2-provider as appropriate.
        # Developers should use these routes, to maintain compatibility for existing client code
        url(r'^oauth2/', include('openedx.core.djangoapps.oauth_dispatch.urls')),
        # These URLs contain the django-oauth2-provider default behavior.  It exists to provide
        # URLs for django-oauth2-provider to call using reverse() with the oauth2 namespace, and
        # also to maintain support for views that have not yet been wrapped in dispatch views.
        url(r'^oauth2/', include('edx_oauth2_provider.urls', namespace='oauth2')),
        # The /_o/ prefix exists to provide a target for code in django-oauth-toolkit that
        # uses reverse() with the 'oauth2_provider' namespace.  Developers should not access these
        # views directly, but should rather use the wrapped views at /oauth2/
        url(r'^_o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    )

if settings.FEATURES.get('ENABLE_LMS_MIGRATION'):
    urlpatterns += (
        url(r'^migrate/modules$', 'lms_migration.migrate.manage_modulestores'),
        url(r'^migrate/reload/(?P<reload_dir>[^/]+)$', 'lms_migration.migrate.manage_modulestores'),
        url(
            r'^migrate/reload/(?P<reload_dir>[^/]+)/(?P<commit_id>[^/]+)$',
            'lms_migration.migrate.manage_modulestores'
        ),
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
        url(r'^status/', include('openedx.core.djangoapps.service_status.urls')),
    )

if settings.FEATURES.get('ENABLE_INSTRUCTOR_BACKGROUND_TASKS'):
    urlpatterns += (
        url(
            r'^instructor_task_status/$',
            'lms.djangoapps.instructor_task.views.instructor_task_status',
            name='instructor_task_status'
        ),
    )

if settings.FEATURES.get('RUN_AS_ANALYTICS_SERVER_ENABLED'):
    urlpatterns += (
        url(r'^edinsights_service/', include('edinsights.core.urls')),
    )

if settings.FEATURES.get('ENABLE_DEBUG_RUN_PYTHON'):
    urlpatterns += (
        url(r'^debug/run_python$', 'debug.views.run_python'),
    )

urlpatterns += (
    url(r'^debug/show_parameters$', 'debug.views.show_parameters'),
)


# Third-party auth.
if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    urlpatterns += (
        url(r'', include('third_party_auth.urls')),
        url(r'api/third_party_auth/', include('third_party_auth.api.urls')),
        # NOTE: The following login_oauth_token endpoint is DEPRECATED.
        # Please use the exchange_access_token endpoint instead.
        url(r'^login_oauth_token/(?P<backend>[^/]+)/$', 'student.views.login_oauth_token'),
    )

# OAuth token exchange
if settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    urlpatterns += (
        url(
            r'^oauth2/login/$',
            LoginWithAccessTokenView.as_view(),
            name="login_with_access_token"
        ),
    )

# Certificates
urlpatterns += (
    url(r'^certificates/', include('certificates.urls', app_name="certificates", namespace="certificates")),

    # Backwards compatibility with XQueue, which uses URLs that are not prefixed with /certificates/
    url(r'^update_certificate$', 'certificates.views.update_certificate'),
    url(r'^update_example_certificate$', 'certificates.views.update_example_certificate'),
    url(r'^request_certificate$', 'certificates.views.request_certificate'),

    # REST APIs
    url(r'^api/certificates/',
        include('lms.djangoapps.certificates.apis.urls', namespace='certificates_api')),
)

# XDomain proxy
urlpatterns += (
    url(r'^xdomain_proxy.html$', 'cors_csrf.views.xdomain_proxy', name='xdomain_proxy'),
)

# Custom courses on edX (CCX) URLs
if settings.FEATURES["CUSTOM_COURSES_EDX"]:
    urlpatterns += (
        url(r'^courses/{}/'.format(settings.COURSE_ID_PATTERN),
            include('ccx.urls')),
        url(r'^api/ccx/', include('lms.djangoapps.ccx.api.urls', namespace='ccx_api')),
    )

# Access to courseware as an LTI provider
if settings.FEATURES.get("ENABLE_LTI_PROVIDER"):
    urlpatterns += (
        url(r'^lti_provider/', include('lti_provider.urls')),
    )

urlpatterns += (
    url(r'config/self_paced', ConfigurationModelCurrentAPIView.as_view(model=SelfPacedConfiguration)),
    url(r'config/programs', ConfigurationModelCurrentAPIView.as_view(model=ProgramsApiConfig)),
    url(r'config/catalog', ConfigurationModelCurrentAPIView.as_view(model=CatalogIntegration)),
)

urlpatterns = patterns(*urlpatterns)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.PROFILE_IMAGE_BACKEND['options']['base_url'],
        document_root=settings.PROFILE_IMAGE_BACKEND['options']['location']
    )

urlpatterns += url(r'^template/(?P<template>.+)$', 'openedx.core.djangoapps.debug.views.show_reference_template'),

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += (
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

# include into our URL patterns the HTTP REST API that comes with edx-proctoring.
urlpatterns += (
    url(r'^api/', include('edx_proctoring.urls')),
)

if settings.FEATURES.get('ENABLE_FINANCIAL_ASSISTANCE_FORM'):
    urlpatterns += (
        url(
            r'^financial-assistance/$',
            'courseware.views.views.financial_assistance',
            name='financial_assistance'
        ),
        url(
            r'^financial-assistance/apply/$',
            'courseware.views.views.financial_assistance_form',
            name='financial_assistance_form'
        ),
        url(
            r'^financial-assistance/submit/$',
            'courseware.views.views.financial_assistance_request',
            name='submit_financial_assistance_request'
        )
    )
