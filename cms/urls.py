from django.conf import settings
from django.conf.urls import patterns, include, url
# There is a course creators admin table.
from ratelimitbackend import admin

from cms.djangoapps.contentstore.views.program import ProgramAuthoringView, ProgramsIdTokenView
from cms.djangoapps.contentstore.views.organization import OrganizationListView

admin.autodiscover()

# Pattern to match a course key or a library key
COURSELIKE_KEY_PATTERN = r'(?P<course_key_string>({}|{}))'.format(
    r'[^/]+/[^/]+/[^/]+', r'[^/:]+:[^/+]+\+[^/+]+(\+[^/]+)?'
)
# Pattern to match a library key only
LIBRARY_KEY_PATTERN = r'(?P<library_key_string>library-v1:[^/+]+\+[^/+]+)'

urlpatterns = patterns(
    '',

    url(r'', include('student.urls')),

    url(r'^transcripts/upload$', 'contentstore.views.upload_transcripts', name='upload_transcripts'),
    url(r'^transcripts/download$', 'contentstore.views.download_transcripts', name='download_transcripts'),
    url(r'^transcripts/check$', 'contentstore.views.check_transcripts', name='check_transcripts'),
    url(r'^transcripts/choose$', 'contentstore.views.choose_transcripts', name='choose_transcripts'),
    url(r'^transcripts/replace$', 'contentstore.views.replace_transcripts', name='replace_transcripts'),
    url(r'^transcripts/rename$', 'contentstore.views.rename_transcripts', name='rename_transcripts'),
    url(r'^transcripts/save$', 'contentstore.views.save_transcripts', name='save_transcripts'),

    url(r'^preview/xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        'contentstore.views.preview_handler', name='preview_handler'),

    url(r'^xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        'contentstore.views.component_handler', name='component_handler'),

    url(r'^xblock/resource/(?P<block_type>[^/]*)/(?P<uri>.*)$',
        'openedx.core.djangoapps.common_views.xblock.xblock_resource', name='xblock_resource_url'),

    url(r'^not_found$', 'contentstore.views.not_found', name='not_found'),
    url(r'^server_error$', 'contentstore.views.server_error', name='server_error'),
    url(r'^organizations$', OrganizationListView.as_view(), name='organizations'),

    # noop to squelch ajax errors
    url(r'^event$', 'contentstore.views.event', name='event'),

    url(r'^xmodule/', include('pipeline_js.urls')),
    url(r'^heartbeat$', include('openedx.core.djangoapps.heartbeat.urls')),

    url(r'^user_api/', include('openedx.core.djangoapps.user_api.legacy_urls')),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    # User API endpoints
    url(r'^api/user/', include('openedx.core.djangoapps.user_api.urls')),

    # Update session view
    url(
        r'^lang_pref/session_language',
        'openedx.core.djangoapps.lang_pref.views.update_session_language',
        name='session_language'
    ),

    # Darklang View to change the preview language (or dark language)
    url(r'^update_lang/', include('openedx.core.djangoapps.dark_lang.urls', namespace='dark_lang')),
)

# restful api
urlpatterns += patterns(
    'contentstore.views',

    url(r'^$', 'howitworks', name='homepage'),
    url(r'^howitworks$', 'howitworks'),
    url(r'^signup$', 'signup', name='signup'),
    url(r'^signin$', 'login_page', name='login'),
    url(r'^request_course_creator$', 'request_course_creator', name='request_course_creator'),

    url(r'^course_team/{}(?:/(?P<email>.+))?$'.format(COURSELIKE_KEY_PATTERN), 'course_team_handler'),
    url(r'^course_info/{}$'.format(settings.COURSE_KEY_PATTERN), 'course_info_handler'),
    url(
        r'^course_info_update/{}/(?P<provided_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        'course_info_update_handler'
    ),
    url(r'^home/?$', 'course_listing', name='home'),
    url(
        r'^course/{}/search_reindex?$'.format(settings.COURSE_KEY_PATTERN),
        'course_search_index_handler',
        name='course_search_index_handler'
    ),
    url(r'^course/{}?$'.format(settings.COURSE_KEY_PATTERN), 'course_handler', name='course_handler'),
    url(r'^course_notifications/{}/(?P<action_state_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        'course_notifications_handler'),
    url(r'^course_rerun/{}$'.format(settings.COURSE_KEY_PATTERN), 'course_rerun_handler', name='course_rerun_handler'),
    url(r'^container/{}$'.format(settings.USAGE_KEY_PATTERN), 'container_handler'),
    url(r'^orphan/{}$'.format(settings.COURSE_KEY_PATTERN), 'orphan_handler'),
    url(r'^assets/{}/{}?$'.format(settings.COURSE_KEY_PATTERN, settings.ASSET_KEY_PATTERN), 'assets_handler'),
    url(r'^import/{}$'.format(COURSELIKE_KEY_PATTERN), 'import_handler'),
    url(r'^import_status/{}/(?P<filename>.+)$'.format(COURSELIKE_KEY_PATTERN), 'import_status_handler'),
    url(r'^export/{}$'.format(COURSELIKE_KEY_PATTERN), 'export_handler'),
    url(r'^xblock/outline/{}$'.format(settings.USAGE_KEY_PATTERN), 'xblock_outline_handler'),
    url(r'^xblock/container/{}$'.format(settings.USAGE_KEY_PATTERN), 'xblock_container_handler'),
    url(r'^xblock/{}/(?P<view_name>[^/]+)$'.format(settings.USAGE_KEY_PATTERN), 'xblock_view_handler'),
    url(r'^xblock/{}?$'.format(settings.USAGE_KEY_PATTERN), 'xblock_handler'),
    url(r'^tabs/{}$'.format(settings.COURSE_KEY_PATTERN), 'tabs_handler'),
    url(r'^settings/details/{}$'.format(settings.COURSE_KEY_PATTERN), 'settings_handler'),
    url(r'^settings/grading/{}(/)?(?P<grader_index>\d+)?$'.format(settings.COURSE_KEY_PATTERN), 'grading_handler'),
    url(r'^settings/advanced/{}$'.format(settings.COURSE_KEY_PATTERN), 'advanced_settings_handler'),
    url(r'^textbooks/{}$'.format(settings.COURSE_KEY_PATTERN), 'textbooks_list_handler'),
    url(r'^textbooks/{}/(?P<textbook_id>\d[^/]*)$'.format(settings.COURSE_KEY_PATTERN), 'textbooks_detail_handler'),
    url(r'^videos/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN), 'videos_handler'),
    url(r'^video_encodings_download/{}$'.format(settings.COURSE_KEY_PATTERN), 'video_encodings_download'),
    url(r'^group_configurations/{}$'.format(settings.COURSE_KEY_PATTERN), 'group_configurations_list_handler'),
    url(r'^group_configurations/{}/(?P<group_configuration_id>\d+)(/)?(?P<group_id>\d+)?$'.format(
        settings.COURSE_KEY_PATTERN), 'group_configurations_detail_handler'),
    url(r'^api/val/v0/', include('edxval.urls')),
    url(r'^api/tasks/v0/', include('user_tasks.urls')),
)

JS_INFO_DICT = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

if settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES'):
    urlpatterns += (
        url(r'^library/{}?$'.format(LIBRARY_KEY_PATTERN),
            'contentstore.views.library_handler', name='library_handler'),
        url(r'^library/{}/team/$'.format(LIBRARY_KEY_PATTERN),
            'contentstore.views.manage_library_users', name='manage_library_users'),
    )

if settings.FEATURES.get('ENABLE_EXPORT_GIT'):
    urlpatterns += (url(
        r'^export_git/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'contentstore.views.export_git',
        name='export_git',
    ),)

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += patterns(
        '',
        url(r'^status/', include('openedx.core.djangoapps.service_status.urls')),
    )

if settings.FEATURES.get('AUTH_USE_CAS'):
    urlpatterns += (
        url(r'^cas-auth/login/$', 'openedx.core.djangoapps.external_auth.views.cas_login', name="cas-login"),
        url(r'^cas-auth/logout/$', 'django_cas.views.logout', {'next_page': '/'}, name="cas-logout"),
    )

urlpatterns += patterns('', url(r'^admin/', include(admin.site.urls)),)

# enable entrance exams
if settings.FEATURES.get('ENTRANCE_EXAMS'):
    urlpatterns += (
        url(r'^course/{}/entrance_exam/?$'.format(settings.COURSE_KEY_PATTERN), 'contentstore.views.entrance_exam'),
    )

# Enable Web/HTML Certificates
if settings.FEATURES.get('CERTIFICATES_HTML_VIEW'):
    urlpatterns += (
        url(r'^certificates/activation/{}/'.format(settings.COURSE_KEY_PATTERN),
            'contentstore.views.certificates.certificate_activation_handler'),
        url(r'^certificates/{}/(?P<certificate_id>\d+)/signatories/(?P<signatory_id>\d+)?$'.format(
            settings.COURSE_KEY_PATTERN), 'contentstore.views.certificates.signatory_detail_handler'),
        url(r'^certificates/{}/(?P<certificate_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
            'contentstore.views.certificates.certificates_detail_handler'),
        url(r'^certificates/{}$'.format(settings.COURSE_KEY_PATTERN),
            'contentstore.views.certificates.certificates_list_handler')
    )

# Maintenance Dashboard
urlpatterns += patterns(
    '',
    url(r'^maintenance/', include('maintenance.urls', namespace='maintenance')),
)

urlpatterns += (
    # These views use a configuration model to determine whether or not to
    # display the Programs authoring app. If disabled, a 404 is returned.
    url(r'^programs/id_token/$', ProgramsIdTokenView.as_view(), name='programs_id_token'),
    # Drops into the Programs authoring app, which handles its own routing.
    url(r'^program/', ProgramAuthoringView.as_view(), name='programs'),
)

if settings.DEBUG:
    try:
        from .urls_dev import urlpatterns as dev_urlpatterns
        urlpatterns += dev_urlpatterns
    except ImportError:
        pass

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += (
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

# Custom error pages
# These are used by Django to render these error codes. Do not remove.
# pylint: disable=invalid-name
handler404 = 'contentstore.views.render_404'
handler500 = 'contentstore.views.render_500'

# display error page templates, for testing purposes
urlpatterns += (
    url(r'^404$', handler404),
    url(r'^500$', handler500),
)
