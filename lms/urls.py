"""
URLs for LMS
"""

from config_models.views import ConfigurationModelCurrentAPIView
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.admin import autodiscover as django_autodiscover
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from edx_api_doc_tools import make_docs_urls
from edx_django_utils.plugins import get_plugin_url_patterns
from ratelimitbackend import admin

from lms.djangoapps.branding import views as branding_views
from lms.djangoapps.debug import views as debug_views
from lms.djangoapps.certificates import views as certificates_views
from lms.djangoapps.courseware.masquerade import MasqueradeView
from lms.djangoapps.courseware.module_render import (
    handle_xblock_callback,
    handle_xblock_callback_noauth,
    xblock_view,
    xqueue_callback
)
from lms.djangoapps.courseware.views import views as courseware_views
from lms.djangoapps.courseware.views.index import CoursewareIndex
from lms.djangoapps.courseware.views.views import CourseTabView, EnrollStaffView, StaticCourseTabView
from lms.djangoapps.discussion import views as discussion_views
from lms.djangoapps.discussion.config.settings import is_forum_daily_digest_enabled
from lms.djangoapps.discussion.notification_prefs import views as notification_prefs_views
from lms.djangoapps.instructor.views import instructor_dashboard as instructor_dashboard_views
from lms.djangoapps.instructor_task import views as instructor_task_views
from lms.djangoapps.staticbook import views as staticbook_views
from lms.djangoapps.static_template_view import views as static_template_view_views
from openedx.core.apidocs import api_info
from openedx.core.djangoapps.auth_exchange.views import LoginWithAccessTokenView
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.common_views.xblock import xblock_resource
from openedx.core.djangoapps.cors_csrf import views as cors_csrf_views
from openedx.core.djangoapps.course_groups import views as course_groups_views
from openedx.core.djangoapps.debug import views as openedx_debug_views
from openedx.core.djangoapps.django_comment_common.models import ForumsConfig
from openedx.core.djangoapps.lang_pref import views as lang_pref_views
from openedx.core.djangoapps.password_policy import compliance as password_policy_compliance
from openedx.core.djangoapps.password_policy.forms import PasswordPolicyAwareAdminAuthForm
from openedx.core.djangoapps.plugins.constants import ProjectType
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.views.login import redirect_to_lms_login
from openedx.core.djangoapps.verified_track_content import views as verified_track_content_views
from openedx.features.enterprise_support.api import enterprise_enabled
from common.djangoapps.student import views as student_views
from common.djangoapps.util import views as util_views

RESET_COURSE_DEADLINES_NAME = 'reset_course_deadlines'
RENDER_XBLOCK_NAME = 'render_xblock'
COURSE_DATES_NAME = 'dates'

if settings.DEBUG or settings.FEATURES.get('ENABLE_DJANGO_ADMIN_SITE'):
    django_autodiscover()
    admin.site.site_header = _('LMS Administration')
    admin.site.site_title = admin.site.site_header

    if password_policy_compliance.should_enforce_compliance_on_login():
        admin.site.login_form = PasswordPolicyAwareAdminAuthForm

# Custom error pages
# These are used by Django to render these error codes. Do not remove.
# pylint: disable=invalid-name
handler404 = static_template_view_views.render_404
handler500 = static_template_view_views.render_500

notification_prefs_urls = [
    url(r'^notification_prefs/enable/', notification_prefs_views.ajax_enable),
    url(r'^notification_prefs/disable/', notification_prefs_views.ajax_disable),
    url(r'^notification_prefs/status/', notification_prefs_views.ajax_status),

    url(
        r'^notification_prefs/unsubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
        notification_prefs_views.set_subscription,
        {'subscribe': False},
        name='unsubscribe_forum_update',
    ),
    url(
        r'^notification_prefs/resubscribe/(?P<token>[a-zA-Z0-9-_=]+)/',
        notification_prefs_views.set_subscription,
        {'subscribe': True},
        name='resubscribe_forum_update',
    ),
]


urlpatterns = [
    url(r'^$', branding_views.index, name='root'),  # Main marketing page, or redirect to courseware

    url(r'', include('common.djangoapps.student.urls')),
    # TODO: Move lms specific student views out of common code
    url(r'^dashboard/?$', student_views.student_dashboard, name='dashboard'),
    url(r'^change_enrollment$', student_views.change_enrollment, name='change_enrollment'),

    # Event tracking endpoints
    url(r'', include('common.djangoapps.track.urls')),

    # Static template view endpoints like blog, faq, etc.
    url(r'', include('lms.djangoapps.static_template_view.urls')),

    url(r'^heartbeat', include('openedx.core.djangoapps.heartbeat.urls')),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    # Enrollment API RESTful endpoints
    url(r'^api/enrollment/v1/', include('openedx.core.djangoapps.enrollments.urls')),

    # Entitlement API RESTful endpoints
    url(
        r'^api/entitlements/',
        include(
            ('common.djangoapps.entitlements.rest_api.urls', 'common.djangoapps.entitlements'),
            namespace='entitlements_api',
        ),
    ),

    # Demographics API RESTful endpoints
    url(r'^api/demographics/', include('openedx.core.djangoapps.demographics.rest_api.urls')),

    # Courseware search endpoints
    url(r'^search/', include('search.urls')),

    # Course API
    url(r'^api/courses/', include('lms.djangoapps.course_api.urls')),

    # User API endpoints
    url(r'^api/user/', include('openedx.core.djangoapps.user_api.urls')),
    # Note: these are older versions of the User API that will eventually be
    # subsumed by api/user listed above.
    url(r'', include('openedx.core.djangoapps.user_api.legacy_urls')),

    # Profile Images API endpoints
    url(r'^api/profile_images/', include('openedx.core.djangoapps.profile_images.urls')),

    # Video Abstraction Layer used to allow video teams to manage video assets
    # independently of courseware. https://github.com/edx/edx-val
    url(r'^api/val/v0/', include('edxval.urls')),

    url(
        r'^api/commerce/',
        include(
            ('lms.djangoapps.commerce.api.urls', 'lms.djangoapps.commerce'),
            namespace='commerce_api',
        ),
    ),
    url(r'^api/credit/', include('openedx.core.djangoapps.credit.urls')),
    url(r'^api/toggles/', include('openedx.core.djangoapps.waffle_utils.urls')),
    url(r'^rss_proxy/', include('lms.djangoapps.rss_proxy.urls')),
    url(r'^api/organizations/', include('organizations.urls', namespace='organizations')),

    url(r'^catalog/', include(('openedx.core.djangoapps.catalog.urls', 'openedx.core.djangoapps.catalog'),
                              namespace='catalog')),

    # Update session view
    url(r'^lang_pref/session_language', lang_pref_views.update_session_language, name='session_language'),

    # Multiple course modes and identity verification
    url(
        r'^course_modes/',
        include('common.djangoapps.course_modes.urls'),
    ),
    url(
        r'^api/course_modes/',
        include(
            ('common.djangoapps.course_modes.rest_api.urls', 'common.djangoapps.course_mods'),
            namespace='course_modes_api',
        )
    ),

    url(r'^verify_student/', include('lms.djangoapps.verify_student.urls')),

    # URLs for managing dark launches of languages
    url(r'^update_lang/', include(('openedx.core.djangoapps.dark_lang.urls', 'openedx.core.djangoapps.dark_lang'),
                                  namespace='dark_lang')),

    # For redirecting to help pages.
    url(r'^help_token/', include('help_tokens.urls')),

    # URLs for API access management
    url(r'^api-admin/', include(('openedx.core.djangoapps.api_admin.urls', 'openedx.core.djangoapps.api_admin'),
                                namespace='api_admin')),

    url(r'^dashboard/', include('lms.djangoapps.learner_dashboard.urls')),
    url(
        r'^api/experiments/',
        include(
            ('lms.djangoapps.experiments.urls', 'lms.djangoapps.experiments'),
            namespace='api_experiments',
        ),
    ),
    url(r'^api/discounts/', include(('openedx.features.discounts.urls', 'openedx.features.discounts'),
                                    namespace='api_discounts')),

    url(r'', include(('openedx.features.edly.urls', 'openedx.features.edly'), namespace='edly_app_urls')),
    url(r'^api/v1/courses/', include('openedx.features.edly.api.urls')),
]

if settings.FEATURES.get('ENABLE_MOBILE_REST_API'):
    urlpatterns += [
        url(r'^api/mobile/(?P<api_version>v(1|0.5))/', include('lms.djangoapps.mobile_api.urls')),
        url(r'^api/mobile/v1/', include('openedx.features.edly.api.urls')),
    ]

if settings.FEATURES.get('ENABLE_OPENBADGES'):
    urlpatterns += [
        url(r'^api/badges/v1/', include(('lms.djangoapps.badges.api.urls', 'badges'), namespace='badges_api')),
    ]

urlpatterns += [
    url(r'^openassessment/fileupload/', include('openassessment.fileupload.urls')),
]

# sysadmin dashboard, to see what courses are loaded, to delete & load courses
if settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'):
    urlpatterns += [
        url(r'^sysadmin/', include('lms.djangoapps.dashboard.sysadmin_urls')),
    ]

urlpatterns += [
    url(r'^support/', include('lms.djangoapps.support.urls')),
]

# Favicon
favicon_path = configuration_helpers.get_value('favicon_path', settings.FAVICON_PATH)  # pylint: disable=invalid-name
urlpatterns += [
    url(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + favicon_path, permanent=True)),
]

# Multicourse wiki (Note: wiki urls must be above the courseware ones because of
# the custom tab catch-all)
if settings.WIKI_ENABLED:
    from wiki.urls import get_pattern as wiki_pattern
    from lms.djangoapps.course_wiki import views as course_wiki_views
    from django_notify.urls import get_pattern as notify_pattern

    wiki_url_patterns, wiki_app_name = wiki_pattern()
    notify_url_patterns, notify_app_name = notify_pattern()

    urlpatterns += [
        # First we include views from course_wiki that we use to override the default views.
        # They come first in the urlpatterns so they get resolved first
        url('^wiki/create-root/$', course_wiki_views.root_create, name='root_create'),
        url(r'^wiki/', include((wiki_url_patterns, wiki_app_name), namespace='wiki')),
        url(r'^notify/', include((notify_url_patterns, notify_app_name), namespace='notify')),

        # These urls are for viewing the wiki in the context of a course. They should
        # never be returned by a reverse() so they come after the other url patterns
        url(r'^courses/{}/course_wiki/?$'.format(settings.COURSE_ID_PATTERN),
            course_wiki_views.course_wiki_redirect, name='course_wiki'),
        url(r'^courses/{}/wiki/'.format(settings.COURSE_KEY_REGEX),
            include((wiki_url_patterns, 'course_wiki_do_not_reverse'), namespace='course_wiki_do_not_reverse')),

        # Include edly panel app URL's
        url(r'^api/edly_panel/', include('edly_panel_app.api.urls', namespace='edly_panel_api')),
    ]

urlpatterns += [
    # jump_to URLs for direct access to a location in the course
    url(
        r'^courses/{}/jump_to/(?P<location>.*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.jump_to,
        name='jump_to',
    ),
    url(
        r'^courses/{}/jump_to_id/(?P<module_id>.*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.jump_to_id,
        name='jump_to_id',
    ),

    # xblock Handler APIs
    url(
        r'^courses/{course_key}/xblock/{usage_key}/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(
            course_key=settings.COURSE_ID_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN,
        ),
        handle_xblock_callback,
        name='xblock_handler',
    ),
    url(
        r'^courses/{course_key}/xblock/{usage_key}/handler_noauth/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$'.format(
            course_key=settings.COURSE_ID_PATTERN,
            usage_key=settings.USAGE_ID_PATTERN,
        ),
        handle_xblock_callback_noauth,
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
        xblock_view,
        name='xblock_view',
    ),

    # xblock Rendering View URL
    # URL to provide an HTML view of an xBlock. The view type (e.g., student_view) is
    # passed as a 'view' parameter to the URL.
    # Note: This is not an API. Compare this with the xblock_view API above.
    url(
        r'^xblock/{usage_key_string}$'.format(usage_key_string=settings.USAGE_KEY_PATTERN),
        courseware_views.render_xblock,
        name=RENDER_XBLOCK_NAME,
    ),

    # xblock Resource URL
    url(
        r'xblock/resource/(?P<block_type>[^/]+)/(?P<uri>.*)$',
        xblock_resource,
        name='xblock_resource_url',
    ),

    # New (Blockstore-based) XBlock REST API
    url(r'', include(('openedx.core.djangoapps.xblock.rest_api.urls', 'openedx.core.djangoapps.xblock'),
                     namespace='xblock_api')),

    url(
        r'^courses/{}/xqueue/(?P<userid>[^/]*)/(?P<mod_id>.*?)/(?P<dispatch>[^/]*)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        xqueue_callback,
        name='xqueue_callback',
    ),

    # TODO: These views need to be updated before they work
    url(r'^calculate$', util_views.calculate),

    url(
        r'^reset_deadlines$',
        util_views.reset_course_deadlines,
        name=RESET_COURSE_DEADLINES_NAME,
    ),

    url(r'^courses/?$', branding_views.courses, name='courses'),

    # About the course
    url(
        r'^courses/{}/about$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.course_about,
        name='about_course',
    ),
    url(
        r'^courses/yt_video_metadata$',
        courseware_views.yt_video_metadata,
        name='yt_video_metadata',
    ),
    url(
        r'^courses/{}/enroll_staff$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        EnrollStaffView.as_view(),
        name='enroll_staff',
    ),

    # Inside the course
    url(
        r'^courses/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.course_info,
        name='course_root',
    ),
    url(
        r'^courses/{}/info$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.course_info,
        name='info',
    ),
    # TODO arjun remove when custom tabs in place, see courseware/courses.py
    url(
        r'^courses/{}/syllabus$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.syllabus,
        name='syllabus',
    ),

    # Survey associated with a course
    url(
        r'^courses/{}/survey$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.course_survey,
        name='course_survey',
    ),

    url(
        r'^courses/{}/book/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.index,
        name='book',
    ),
    url(
        r'^courses/{}/book/(?P<book_index>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.index,
        name='book',
    ),

    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.pdf_index,
        name='pdf_book',
    ),
    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.pdf_index,
        name='pdf_book',
    ),

    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.pdf_index,
        name='pdf_book',
    ),
    url(
        r'^courses/{}/pdfbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/(?P<page>\d+)$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.pdf_index,
        name='pdf_book',
    ),

    url(
        r'^courses/{}/htmlbook/(?P<book_index>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.html_index,
        name='html_book',
    ),
    url(
        r'^courses/{}/htmlbook/(?P<book_index>\d+)/chapter/(?P<chapter>\d+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        staticbook_views.html_index,
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
        courseware_views.progress,
        name='progress',
    ),

    # dates page
    url(
        r'^courses/{}/dates'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.dates,
        name=COURSE_DATES_NAME,
    ),

    # Takes optional student_id for instructor use--shows profile as that student sees it.
    url(
        r'^courses/{}/progress/(?P<student_id>[^/]*)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.progress,
        name='student_progress',
    ),

    url(
        r'^programs/{}/about'.format(
            r'(?P<program_uuid>[0-9a-f-]+)',
        ),
        courseware_views.program_marketing,
        name='program_marketing_view',
    ),

    # For the instructor
    url(
        r'^courses/{}/instructor$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        instructor_dashboard_views.instructor_dashboard_2,
        name='instructor_dashboard',
    ),

    url(
        r'^courses/{}/set_course_mode_price$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        instructor_dashboard_views.set_course_mode_price,
        name='set_course_mode_price',
    ),

    # Discussions Management
    url(
        r'^courses/{}/discussions/settings$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        discussion_views.course_discussions_settings_handler,
        name='course_discussions_settings',
    ),

    # Cohorts management API
    url(r'^api/cohorts/', include(
        ('openedx.core.djangoapps.course_groups.urls', 'openedx.core.djangoapps.course_groups'),
        namespace='api_cohorts')),

    # Cohorts management
    url(
        r'^courses/{}/cohorts/settings$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.course_cohort_settings_handler,
        name='course_cohort_settings',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)?$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.cohort_handler,
        name='cohorts',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.users_in_cohort,
        name='list_cohort',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/add$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.add_users_to_cohort,
        name='add_to_cohort',
    ),
    url(
        r'^courses/{}/cohorts/(?P<cohort_id>[0-9]+)/delete$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.remove_user_from_cohort,
        name='remove_from_cohort',
    ),
    url(
        r'^courses/{}/cohorts/debug$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        course_groups_views.debug_cohort_mgmt,
        name='debug_cohort_mgmt',
    ),
    url(
        r'^courses/{}/discussion/topics$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        discussion_views.discussion_topics,
        name='discussion_topics',
    ),
    url(
        r'^courses/{}/verified_track_content/settings'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        verified_track_content_views.cohorting_settings,
        name='verified_track_cohorting',
    ),

    # LTI endpoints listing
    url(
        r'^courses/{}/lti_rest_endpoints/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.get_course_lti_endpoints,
        name='lti_rest_endpoints',
    ),

    # Student Notes
    url(
        r'^courses/{}/edxnotes/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('lms.djangoapps.edxnotes.urls'),
        name='edxnotes_endpoints',
    ),

    # Student Notes API
    url(
        r'^api/edxnotes/v1/',
        include('lms.djangoapps.edxnotes.api_urls'),
    ),

    # Branding API
    url(
        r'^api/branding/v1/',
        include('lms.djangoapps.branding.api_urls')
    ),

    # Course experience
    url(
        r'^courses/{}/course/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('openedx.features.course_experience.urls'),
    ),

    # Course bookmarks UI in LMS
    url(
        r'^courses/{}/bookmarks/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('openedx.features.course_bookmarks.urls'),
    ),

    # Calendar Sync UI in LMS
    url(
        r'^courses/{}/'.format(settings.COURSE_ID_PATTERN,),
        include('openedx.features.calendar_sync.urls'),
    ),

    # Course search
    url(
        r'^courses/{}/search/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('openedx.features.course_search.urls'),
    ),

    # Learner profile
    url(
        r'^u/',
        include('openedx.features.learner_profile.urls'),
    ),
    # Subscriptions
    url(
        r'^api/subscriptions/',
        include(
            'openedx.features.subscriptions.api.v1.urls',
            namespace='subscriptions_api',
        )
    ),

    # Course Rating
    url(
        r'^api/v1/',
        include(
            'openedx.features.course_rating.api.v1.urls',
            namespace='course_rating_api',
        )
    ),
]

if settings.FEATURES.get('ENABLE_TEAMS'):
    # Teams endpoints
    urlpatterns += [
        url(
            r'^api/team/',
            include('lms.djangoapps.teams.api_urls')
        ),
        url(
            r'^courses/{}/teams/'.format(
                settings.COURSE_ID_PATTERN,
            ),
            include('lms.djangoapps.teams.urls'),
            name='teams_endpoints',
        ),
    ]

# allow course staff to change to student view of courseware
if settings.FEATURES.get('ENABLE_MASQUERADE'):
    urlpatterns += [
        url(
            r'^courses/{}/masquerade$'.format(
                settings.COURSE_KEY_PATTERN,
            ),
            MasqueradeView.as_view(),
            name='masquerade_update',
        ),
    ]

urlpatterns += [
    url(
        r'^courses/{}/generate_user_cert'.format(
            settings.COURSE_ID_PATTERN,
        ),
        courseware_views.generate_user_cert,
        name='generate_user_cert',
    ),
]

# discussion forums live within courseware, so courseware must be enabled first
if settings.FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
    urlpatterns += [
        url(
            r'^api/discussion/',
            include('lms.djangoapps.discussion.rest_api.urls')
        ),
        url(
            r'^courses/{}/discussion/'.format(
                settings.COURSE_ID_PATTERN,
            ),
            include('lms.djangoapps.discussion.django_comment_client.urls')
        ),
    ]

if is_forum_daily_digest_enabled():
    urlpatterns += notification_prefs_urls

urlpatterns += [
    url(r'^bulk_email/', include('lms.djangoapps.bulk_email.urls')),
]

urlpatterns += [
    url(
        r'^courses/{}/tab/(?P<tab_type>[^/]+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CourseTabView.as_view(),
        name='course_tab_view',
    ),
]

urlpatterns += [
    # This MUST be the last view in the courseware--it's a catch-all for custom tabs.
    url(
        r'^courses/{}/(?P<tab_slug>[^/]+)/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        StaticCourseTabView.as_view(),
        name='static_tab',
    ),
]

if settings.FEATURES.get('ENABLE_STUDENT_HISTORY_VIEW'):
    urlpatterns += [
        url(
            r'^courses/{}/submission_history/(?P<student_username>[^/]*)/(?P<location>.*?)$'.format(
                settings.COURSE_ID_PATTERN
            ),
            courseware_views.submission_history,
            name='submission_history',
        ),
    ]

if settings.DEBUG or settings.FEATURES.get('ENABLE_DJANGO_ADMIN_SITE'):
    # Jasmine and admin

    # The password pages in the admin tool are disabled so that all password
    # changes go through our user portal and follow complexity requirements.
    # The form to change another user's password is conditionally enabled
    # for backwards compatibility.
    if not settings.FEATURES.get('ENABLE_CHANGE_USER_PASSWORD_ADMIN'):
        urlpatterns += [
            url(r'^admin/auth/user/\d+/password/$', handler404),
        ]
    urlpatterns += [
        url(r'^admin/password_change/$', handler404),
        # We are enforcing users to login through third party auth in site's
        # login page so we are disabling the admin panel's login page.
        url(r'^admin/login/$', redirect_to_lms_login),
        url(r'^admin/', admin.site.urls),
    ]

if configuration_helpers.get_value('ENABLE_BULK_ENROLLMENT_VIEW', settings.FEATURES.get('ENABLE_BULK_ENROLLMENT_VIEW')):
    urlpatterns += [
        url(r'^api/bulk_enroll/v1/', include('lms.djangoapps.bulk_enroll.urls')),
    ]

# Course goals
urlpatterns += [
    url(r'^api/course_goals/', include(('lms.djangoapps.course_goals.urls', 'lms.djangoapps.course_goals'),
                                       namespace='course_goals_api')),
]

# Embargo
if settings.FEATURES.get('EMBARGO'):
    urlpatterns += [
        url(r'^embargo/', include(('openedx.core.djangoapps.embargo.urls', 'openedx.core.djangoapps.embargo'),
                                  namespace='embargo')),
        url(r'^api/embargo/', include(('openedx.core.djangoapps.embargo.urls', 'openedx.core.djangoapps.embargo'),
                                      namespace='api_embargo')),
    ]

# Survey Djangoapp
urlpatterns += [
    url(r'^survey/', include('lms.djangoapps.survey.urls')),
]

if settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    urlpatterns += [
        # These URLs dispatch to django-oauth-toolkit or django-oauth2-provider as appropriate.
        # Developers should use these routes, to maintain compatibility for existing client code
        url(r'^oauth2/', include('openedx.core.djangoapps.oauth_dispatch.urls')),
        # The /_o/ prefix exists to provide a target for code in django-oauth-toolkit that
        # uses reverse() with the 'oauth2_provider' namespace.  Developers should not access these
        # views directly, but should rather use the wrapped views at /oauth2/
        url(r'^_o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += [
        url(r'^status/', include('openedx.core.djangoapps.service_status.urls')),
    ]

if settings.FEATURES.get('ENABLE_INSTRUCTOR_BACKGROUND_TASKS'):
    urlpatterns += [
        url(
            r'^instructor_task_status/$',
            instructor_task_views.instructor_task_status,
            name='instructor_task_status'
        ),
    ]

if settings.FEATURES.get('ENABLE_DEBUG_RUN_PYTHON'):
    urlpatterns += [
        url(r'^debug/run_python$', debug_views.run_python),
    ]

urlpatterns += [
    url(r'^debug/show_parameters$', debug_views.show_parameters),
]

# Third-party auth.
if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'):
    urlpatterns += [
        url(r'', include('common.djangoapps.third_party_auth.urls')),
        url(r'^api/third_party_auth/', include('common.djangoapps.third_party_auth.api.urls')),
    ]

# Enterprise
if enterprise_enabled():
    urlpatterns += [
        url(r'', include('enterprise.urls')),
    ]

# OAuth token exchange
if settings.FEATURES.get('ENABLE_OAUTH2_PROVIDER'):
    urlpatterns += [
        url(
            r'^oauth2/login/$',
            LoginWithAccessTokenView.as_view(),
            name='login_with_access_token'
        ),
    ]

# Certificates
urlpatterns += [
    url(r'^certificates/', include('lms.djangoapps.certificates.urls')),

    # Backwards compatibility with XQueue, which uses URLs that are not prefixed with /certificates/
    url(r'^update_certificate$', certificates_views.update_certificate, name='update_certificate'),
    url(r'^update_example_certificate$', certificates_views.update_example_certificate,
        name='update_example_certificate'),
    url(r'^request_certificate$', certificates_views.request_certificate,
        name='request_certificate'),

    # REST APIs
    url(r'^api/certificates/',
        include(('lms.djangoapps.certificates.apis.urls', 'lms.djangoapps.certificates'),
                namespace='certificates_api')),
]

# XDomain proxy
urlpatterns += [
    url(r'^xdomain_proxy.html$', cors_csrf_views.xdomain_proxy, name='xdomain_proxy'),
]

# Custom courses on edX (CCX) URLs
if settings.FEATURES.get('CUSTOM_COURSES_EDX'):
    urlpatterns += [
        url(r'^courses/{}/'.format(settings.COURSE_ID_PATTERN),
            include('lms.djangoapps.ccx.urls')),
        url(r'^api/ccx/', include(('lms.djangoapps.ccx.api.urls', 'lms.djangoapps.ccx'), namespace='ccx_api')),
    ]

# Access to courseware as an LTI provider
if settings.FEATURES.get('ENABLE_LTI_PROVIDER'):
    urlpatterns += [
        url(r'^lti_provider/', include('lms.djangoapps.lti_provider.urls')),
    ]

urlpatterns += [
    url(r'^config/self_paced', ConfigurationModelCurrentAPIView.as_view(model=SelfPacedConfiguration)),
    url(r'^config/programs', ConfigurationModelCurrentAPIView.as_view(model=ProgramsApiConfig)),
    url(r'^config/catalog', ConfigurationModelCurrentAPIView.as_view(model=CatalogIntegration)),
    url(r'^config/forums', ConfigurationModelCurrentAPIView.as_view(model=ForumsConfig)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.PROFILE_IMAGE_BACKEND['options']['base_url'],
        document_root=settings.PROFILE_IMAGE_BACKEND['options']['location']
    )

# UX reference templates
urlpatterns += [
    url(r'^template/(?P<template>.+)$', openedx_debug_views.show_reference_template),
]

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

if settings.FEATURES.get('ENABLE_FINANCIAL_ASSISTANCE_FORM'):
    urlpatterns += [
        url(
            r'^financial-assistance/$',
            courseware_views.financial_assistance,
            name='financial_assistance'
        ),
        url(
            r'^financial-assistance/apply/$',
            courseware_views.financial_assistance_form,
            name='financial_assistance_form'
        ),
        url(
            r'^financial-assistance/submit/$',
            courseware_views.financial_assistance_request,
            name='submit_financial_assistance_request'
        )
    ]

# Branch.io Text Me The App
if settings.BRANCH_IO_KEY:
    urlpatterns += [
        url(r'^text-me-the-app', student_views.text_me_the_app, name='text_me_the_app'),
    ]

# API docs.
urlpatterns += make_docs_urls(api_info)

# edx-drf-extensions csrf app
urlpatterns += [
    url(r'', include('csrf.urls')),
]

if 'openedx.testing.coverage_context_listener' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'coverage_context', include('openedx.testing.coverage_context_listener.urls'))
    ]

urlpatterns.append(
    url(
        r'^api/learning_sequences/',
        include(
            ('openedx.core.djangoapps.content.learning_sequences.urls', 'learning_sequences'),
            namespace='learning_sequences'
        ),
    ),
)

urlpatterns.extend(get_plugin_url_patterns(ProjectType.LMS))

# Course Home API urls
urlpatterns += [
    url(r'^api/course_home/', include('lms.djangoapps.course_home_api.urls')),
]

# Course Experience API urls
urlpatterns += [
    url(r'^api/course_experience/', include('openedx.features.course_experience.api.v1.urls')),
]
