from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.admin import autodiscover as django_autodiscover
from django.utils.translation import ugettext_lazy as _
from ratelimitbackend import admin

from cms.djangoapps.contentstore.views.organization import OrganizationListView
from contentstore.views import (
    upload_transcripts,
    download_transcripts,
    check_transcripts,
    choose_transcripts,
    replace_transcripts,
    rename_transcripts,
    save_transcripts,
    preview_handler,
    component_handler,
    not_found,
    server_error,
    event,
    library_handler,
    manage_library_users,
    export_git,
    entrance_exam,
    render_404,
    render_500,
    howitworks,
    signup,
    login_page,
    request_course_creator,
    course_team_handler,
    course_info_handler,
    course_info_update_handler,
    course_listing,
    course_search_index_handler,
    course_handler,
    course_notifications_handler,
    course_rerun_handler,
    container_handler,
    orphan_handler,
    assets_handler,
    import_handler,
    import_status_handler,
    export_handler,
    export_output_handler,
    export_status_handler,
    xblock_outline_handler,
    xblock_container_handler,
    xblock_view_handler,
    xblock_handler,
    tabs_handler,
    settings_handler,
    grading_handler,
    advanced_settings_handler,
    textbooks_list_handler,
    textbooks_detail_handler,
    videos_handler,
    video_images_handler,
    video_encodings_download,
    group_configurations_list_handler,
    group_configurations_detail_handler,
)
from openedx.core.djangoapps.common_views.xblock import xblock_resource
from openedx.core.djangoapps.lang_pref.views import update_session_language
from openedx.core.djangoapps.external_auth.views import cas_login
from django_cas.views import logout as cas_logout
from contentstore.views.certificates import (
    certificate_activation_handler,
    signatory_detail_handler,
    certificates_detail_handler,
    certificates_list_handler
)
from openedx.core.djangoapps.debug.views import show_reference_template

django_autodiscover()
admin.site.site_header = _('Studio Administration')
admin.site.site_title = admin.site.site_header

# Pattern to match a course key or a library key
COURSELIKE_KEY_PATTERN = r'(?P<course_key_string>({}|{}))'.format(
    r'[^/]+/[^/]+/[^/]+', r'[^/:]+:[^/+]+\+[^/+]+(\+[^/]+)?'
)

# Pattern to match a library key only
LIBRARY_KEY_PATTERN = r'(?P<library_key_string>library-v1:[^/+]+\+[^/+]+)'

urlpatterns = [
    url(r'', include('student.urls')),

    url(r'^transcripts/upload$', upload_transcripts, name='upload_transcripts'),
    url(r'^transcripts/download$', download_transcripts, name='download_transcripts'),
    url(r'^transcripts/check$', check_transcripts, name='check_transcripts'),
    url(r'^transcripts/choose$', choose_transcripts, name='choose_transcripts'),
    url(r'^transcripts/replace$', replace_transcripts, name='replace_transcripts'),
    url(r'^transcripts/rename$', rename_transcripts, name='rename_transcripts'),
    url(r'^transcripts/save$', save_transcripts, name='save_transcripts'),

    url(r'^preview/xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        preview_handler, name=preview_handler),

    url(r'^xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        component_handler, name=component_handler),

    url(r'^xblock/resource/(?P<block_type>[^/]*)/(?P<uri>.*)$',
        xblock_resource, name='xblock_resource_url'),

    url(r'^not_found$', not_found, name='not_found'),
    url(r'^server_error$', server_error, name='server_error'),
    url(r'^organizations$', OrganizationListView.as_view(), name='organizations'),

    # noop to squelch ajax errors
    url(r'^event$', event, name='event'),

    url(r'^xmodule/', include('pipeline_js.urls')),
    url(r'^heartbeat$', include('openedx.core.djangoapps.heartbeat.urls')),

    url(r'^user_api/', include('openedx.core.djangoapps.user_api.legacy_urls')),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    # User API endpoints
    url(r'^api/user/', include('openedx.core.djangoapps.user_api.urls')),

    # Update session view
    url(
        r'^lang_pref/session_language',
        update_session_language,
        name='session_language'
    ),

    # Darklang View to change the preview language (or dark language)
    url(r'^update_lang/', include('openedx.core.djangoapps.dark_lang.urls', namespace='dark_lang')),

    # URLs for managing theming
    url(r'^theming/', include('openedx.core.djangoapps.theming.urls', namespace='theming')),

    # For redirecting to help pages.
    url(r'^help_token/', include('help_tokens.urls')),
    url(r'^api/', include('cms.djangoapps.api.urls', namespace='api')),
]

# restful api
urlpatterns += [
    url(r'^$', howitworks, name='homepage'),
    url(r'^howitworks$', howitworks),
    url(r'^signup$', signup, name='signup'),
    url(r'^signin$', login_page, name='login'),
    url(r'^request_course_creator$', request_course_creator, name='request_course_creator'),

    url(r'^course_team/{}(?:/(?P<email>.+))?$'.format(COURSELIKE_KEY_PATTERN), course_team_handler),
    url(r'^course_info/{}$'.format(settings.COURSE_KEY_PATTERN), course_info_handler),
    url(r'^course_info_update/{}/(?P<provided_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        course_info_update_handler),
    url(r'^home/?$', course_listing, name='home'),
    url(r'^course/{}/search_reindex?$'.format(settings.COURSE_KEY_PATTERN),
        course_search_index_handler,
        name='course_search_index_handler'
    ),
    url(r'^course/{}?$'.format(settings.COURSE_KEY_PATTERN), course_handler, name='course_handler'),
    url(r'^course_notifications/{}/(?P<action_state_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        course_notifications_handler),
    url(r'^course_rerun/{}$'.format(settings.COURSE_KEY_PATTERN), course_rerun_handler, name='course_rerun_handler'),
    url(r'^container/{}$'.format(settings.USAGE_KEY_PATTERN), container_handler),
    url(r'^orphan/{}$'.format(settings.COURSE_KEY_PATTERN), orphan_handler),
    url(r'^assets/{}/{}?$'.format(settings.COURSE_KEY_PATTERN, settings.ASSET_KEY_PATTERN), assets_handler),
    url(r'^import/{}$'.format(COURSELIKE_KEY_PATTERN), import_handler),
    url(r'^import_status/{}/(?P<filename>.+)$'.format(COURSELIKE_KEY_PATTERN), import_status_handler),
    # rest api for course import/export
    url(
        r'^api/courses/',
        include('cms.djangoapps.contentstore.api.urls', namespace='courses_api')
    ),
    url(r'^export/{}$'.format(COURSELIKE_KEY_PATTERN), export_handler),
    url(r'^export_output/{}$'.format(COURSELIKE_KEY_PATTERN), export_output_handler),
    url(r'^export_status/{}$'.format(COURSELIKE_KEY_PATTERN), export_status_handler),
    url(r'^xblock/outline/{}$'.format(settings.USAGE_KEY_PATTERN), xblock_outline_handler),
    url(r'^xblock/container/{}$'.format(settings.USAGE_KEY_PATTERN), xblock_container_handler),
    url(r'^xblock/{}/(?P<view_name>[^/]+)$'.format(settings.USAGE_KEY_PATTERN), xblock_view_handler),
    url(r'^xblock/{}?$'.format(settings.USAGE_KEY_PATTERN), xblock_handler),
    url(r'^tabs/{}$'.format(settings.COURSE_KEY_PATTERN), tabs_handler),
    url(r'^settings/details/{}$'.format(settings.COURSE_KEY_PATTERN), settings_handler),
    url(r'^settings/grading/{}(/)?(?P<grader_index>\d+)?$'.format(settings.COURSE_KEY_PATTERN), grading_handler),
    url(r'^settings/advanced/{}$'.format(settings.COURSE_KEY_PATTERN), advanced_settings_handler),
    url(r'^textbooks/{}$'.format(settings.COURSE_KEY_PATTERN), textbooks_list_handler),
    url(r'^textbooks/{}/(?P<textbook_id>\d[^/]*)$'.format(settings.COURSE_KEY_PATTERN), textbooks_detail_handler),
    url(r'^videos/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN), videos_handler),
    url(r'^video_images/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN), video_images_handler),
    url(r'^video_encodings_download/{}$'.format(settings.COURSE_KEY_PATTERN), video_encodings_download),
    url(r'^group_configurations/{}$'.format(settings.COURSE_KEY_PATTERN), group_configurations_list_handler),
    url(r'^group_configurations/{}/(?P<group_configuration_id>\d+)(/)?(?P<group_id>\d+)?$'.format(
        settings.COURSE_KEY_PATTERN), group_configurations_detail_handler),
    url(r'^api/val/v0/', include('edxval.urls')),
    url(r'^api/tasks/v0/', include('user_tasks.urls')),
]

JS_INFO_DICT = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

if settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES'):
    urlpatterns += [
        url(r'^library/{}?$'.format(LIBRARY_KEY_PATTERN),
            library_handler, name='library_handler'),
        url(r'^library/{}/team/$'.format(LIBRARY_KEY_PATTERN),
            manage_library_users, name='manage_library_users'),
    ]

if settings.FEATURES.get('ENABLE_EXPORT_GIT'):
    urlpatterns += [url(
        r'^export_git/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        export_git,
        name='export_git',
    ),]

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += [
        url(r'^status/', include('openedx.core.djangoapps.service_status.urls')),
    ]

if settings.FEATURES.get('AUTH_USE_CAS'):
    urlpatterns += [
        url(r'^cas-auth/login/$', cas_login, name="cas-login"),
        url(r'^cas-auth/logout/$', cas_logout, {'next_page': '/'}, name="cas-logout"),
    ]

urlpatterns += [url(r'^admin/', include(admin.site.urls)),]

# enable entrance exams
if settings.FEATURES.get('ENTRANCE_EXAMS'):
    urlpatterns += [
        url(r'^course/{}/entrance_exam/?$'.format(settings.COURSE_KEY_PATTERN), entrance_exam),
    ]

# Enable Web/HTML Certificates
if settings.FEATURES.get('CERTIFICATES_HTML_VIEW'):
    urlpatterns += [
        url(r'^certificates/activation/{}/'.format(settings.COURSE_KEY_PATTERN), certificate_activation_handler),
        url(r'^certificates/{}/(?P<certificate_id>\d+)/signatories/(?P<signatory_id>\d+)?$'.format(
            settings.COURSE_KEY_PATTERN), signatory_detail_handler),
        url(r'^certificates/{}/(?P<certificate_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
            certificates_detail_handler),
        url(r'^certificates/{}$'.format(settings.COURSE_KEY_PATTERN), certificates_list_handler)
    ]

# Maintenance Dashboard
urlpatterns += [
    url(r'^maintenance/', include('maintenance.urls', namespace='maintenance')),
]

if settings.DEBUG:
    try:
        from .urls_dev import urlpatterns as dev_urlpatterns
        urlpatterns += dev_urlpatterns
    except ImportError:
        pass

    urlpatterns += static(
        settings.VIDEO_IMAGE_SETTINGS['STORAGE_KWARGS']['base_url'],
        document_root=settings.VIDEO_IMAGE_SETTINGS['STORAGE_KWARGS']['location']
    )

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

# UX reference templates
urlpatterns += [
    url(r'^template/(?P<template>.+)$', show_reference_template),
]

# Custom error pages
# These are used by Django to render these error codes. Do not remove.
# pylint: disable=invalid-name
handler404 = render_404
handler500 = render_500

# display error page templates, for testing purposes
urlpatterns += [
    url(r'^404$', handler404),
    url(r'^500$', handler500),
]
