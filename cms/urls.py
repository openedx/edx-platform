"""
Urls of Studio.
"""
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.admin import autodiscover as django_autodiscover
from django.utils.translation import ugettext_lazy as _
from ratelimitbackend import admin

import contentstore.views
import openedx.core.djangoapps.common_views.xblock
import openedx.core.djangoapps.debug.views
import openedx.core.djangoapps.lang_pref.views
from cms.djangoapps.contentstore.views.organization import OrganizationListView
from openedx.core.djangoapps.password_policy import compliance as password_policy_compliance
from openedx.core.djangoapps.password_policy.forms import PasswordPolicyAwareAdminAuthForm
from openedx.core.openapi import schema_view

django_autodiscover()
admin.site.site_header = _('Studio Administration')
admin.site.site_title = admin.site.site_header

if password_policy_compliance.should_enforce_compliance_on_login():
    admin.site.login_form = PasswordPolicyAwareAdminAuthForm

# Custom error pages
# These are used by Django to render these error codes. Do not remove.
# pylint: disable=invalid-name
handler404 = contentstore.views.render_404
handler500 = contentstore.views.render_500

# Pattern to match a course key or a library key
COURSELIKE_KEY_PATTERN = r'(?P<course_key_string>({}|{}))'.format(
    r'[^/]+/[^/]+/[^/]+', r'[^/:]+:[^/+]+\+[^/+]+(\+[^/]+)?'
)

# Pattern to match a library key only
LIBRARY_KEY_PATTERN = r'(?P<library_key_string>library-v1:[^/+]+\+[^/+]+)'

urlpatterns = [
    url(r'', include('openedx.core.djangoapps.user_authn.urls_common')),
    url(r'', include('student.urls')),
    url(r'^transcripts/upload$', contentstore.views.upload_transcripts, name='upload_transcripts'),
    url(r'^transcripts/download$', contentstore.views.download_transcripts, name='download_transcripts'),
    url(r'^transcripts/check$', contentstore.views.check_transcripts, name='check_transcripts'),
    url(r'^transcripts/choose$', contentstore.views.choose_transcripts, name='choose_transcripts'),
    url(r'^transcripts/replace$', contentstore.views.replace_transcripts, name='replace_transcripts'),
    url(r'^transcripts/rename$', contentstore.views.rename_transcripts, name='rename_transcripts'),
    url(r'^preview/xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        contentstore.views.preview_handler, name='preview_handler'),
    url(r'^xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        contentstore.views.component_handler, name='component_handler'),
    url(r'^xblock/resource/(?P<block_type>[^/]*)/(?P<uri>.*)$',
        openedx.core.djangoapps.common_views.xblock.xblock_resource, name='xblock_resource_url'),
    url(r'^not_found$', contentstore.views.not_found, name='not_found'),
    url(r'^server_error$', contentstore.views.server_error, name='server_error'),
    url(r'^organizations$', OrganizationListView.as_view(), name='organizations'),

    # noop to squelch ajax errors
    url(r'^event$', contentstore.views.event, name='event'),
    url(r'^heartbeat', include('openedx.core.djangoapps.heartbeat.urls')),
    url(r'^user_api/', include('openedx.core.djangoapps.user_api.legacy_urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # User API endpoints
    url(r'^api/user/', include('openedx.core.djangoapps.user_api.urls')),

    # Update session view
    url(r'^lang_pref/session_language',
        openedx.core.djangoapps.lang_pref.views.update_session_language,
        name='session_language'
        ),

    # Darklang View to change the preview language (or dark language)
    url(r'^update_lang/', include('openedx.core.djangoapps.dark_lang.urls', namespace='dark_lang')),

    # For redirecting to help pages.
    url(r'^help_token/', include('help_tokens.urls')),
    url(r'^api/', include('cms.djangoapps.api.urls', namespace='api')),

    # restful api
    url(r'^$', contentstore.views.howitworks, name='homepage'),
    url(r'^howitworks$', contentstore.views.howitworks, name='howitworks'),
    url(r'^signup$', contentstore.views.signup, name='signup'),
    url(r'^signin$', contentstore.views.login_page, name='login'),
    url(r'^signin_redirect_to_lms$', contentstore.views.login_redirect_to_lms, name='login_redirect_to_lms'),
    url(r'^request_course_creator$', contentstore.views.request_course_creator, name='request_course_creator'),
    url(r'^course_team/{}(?:/(?P<email>.+))?$'.format(COURSELIKE_KEY_PATTERN),
        contentstore.views.course_team_handler, name='course_team_handler'),
    url(r'^course_info/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.course_info_handler,
        name='course_info_handler'),
    url(r'^course_info_update/{}/(?P<provided_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.course_info_update_handler, name='course_info_update_handler'
        ),
    url(r'^home/?$', contentstore.views.course_listing, name='home'),
    url(r'^course/{}/search_reindex?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.course_search_index_handler,
        name='course_search_index_handler'
        ),
    url(r'^course/{}?$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.course_handler, name='course_handler'),

    url(r'^checklists/{}?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.checklists_handler,
        name='checklists_handler'),

    url(r'^course_notifications/{}/(?P<action_state_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.course_notifications_handler,
        name='course_notifications_handler'),
    url(r'^course_rerun/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.course_rerun_handler,
        name='course_rerun_handler'),
    url(r'^container/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore.views.container_handler,
        name='container_handler'),
    url(r'^orphan/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.orphan_handler,
        name='orphan_handler'),
    url(r'^assets/{}/{}?$'.format(settings.COURSE_KEY_PATTERN, settings.ASSET_KEY_PATTERN),
        contentstore.views.assets_handler,
        name='assets_handler'),
    url(r'^import/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore.views.import_handler,
        name='import_handler'),
    url(r'^import_status/{}/(?P<filename>.+)$'.format(COURSELIKE_KEY_PATTERN),
        contentstore.views.import_status_handler, name='import_status_handler'),
    # rest api for course import/export
    url(r'^api/courses/',
        include('cms.djangoapps.contentstore.api.urls', namespace='courses_api')
        ),
    url(r'^export/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore.views.export_handler,
        name='export_handler'),
    url(r'^export_output/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore.views.export_output_handler,
        name='export_output_handler'),
    url(r'^export_status/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore.views.export_status_handler,
        name='export_status_handler'),
    url(r'^xblock/outline/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore.views.xblock_outline_handler,
        name='xblock_outline_handler'),
    url(r'^xblock/container/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore.views.xblock_container_handler,
        name='xblock_container_handler'),
    url(r'^xblock/{}/(?P<view_name>[^/]+)$'.format(settings.USAGE_KEY_PATTERN), contentstore.views.xblock_view_handler,
        name='xblock_view_handler'),
    url(r'^xblock/{}?$'.format(settings.USAGE_KEY_PATTERN), contentstore.views.xblock_handler,
        name='xblock_handler'),
    url(r'^tabs/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.tabs_handler,
        name='tabs_handler'),
    url(r'^settings/details/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.settings_handler,
        name='settings_handler'),
    url(r'^settings/grading/{}(/)?(?P<grader_index>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.grading_handler, name='grading_handler'),
    url(r'^settings/advanced/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.advanced_settings_handler,
        name='advanced_settings_handler'),
    url(r'^textbooks/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore.views.textbooks_list_handler,
        name='textbooks_list_handler'),
    url(r'^textbooks/{}/(?P<textbook_id>\d[^/]*)$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.textbooks_detail_handler, name='textbooks_detail_handler'),
    url(r'^videos/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.videos_handler, name='videos_handler'),
    url(r'^video_images/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.video_images_handler, name='video_images_handler'),
    url(r'^transcript_preferences/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.transcript_preferences_handler, name='transcript_preferences_handler'),
    url(r'^transcript_credentials/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.transcript_credentials_handler, name='transcript_credentials_handler'),
    url(r'^transcript_download/$', contentstore.views.transcript_download_handler, name='transcript_download_handler'),
    url(r'^transcript_upload/$', contentstore.views.transcript_upload_handler, name='transcript_upload_handler'),
    url(r'^transcript_delete/{}(?:/(?P<edx_video_id>[-\w]+))?(?:/(?P<language_code>[^/]*))?$'.format(
        settings.COURSE_KEY_PATTERN
    ), contentstore.views.transcript_delete_handler, name='transcript_delete_handler'),
    url(r'^video_encodings_download/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.video_encodings_download, name='video_encodings_download'),
    url(r'^group_configurations/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.group_configurations_list_handler,
        name='group_configurations_list_handler'),
    url(r'^group_configurations/{}/(?P<group_configuration_id>\d+)(/)?(?P<group_id>\d+)?$'.format(
        settings.COURSE_KEY_PATTERN), contentstore.views.group_configurations_detail_handler,
        name='group_configurations_detail_handler'),
    url(r'^api/val/v0/', include('edxval.urls')),
    url(r'^api/tasks/v0/', include('user_tasks.urls')),
    url(r'^accessibility$', contentstore.views.accessibility, name='accessibility'),
]

JS_INFO_DICT = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

if settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES'):
    urlpatterns += [
        url(r'^library/{}?$'.format(LIBRARY_KEY_PATTERN),
            contentstore.views.library_handler, name='library_handler'),
        url(r'^library/{}/team/$'.format(LIBRARY_KEY_PATTERN),
            contentstore.views.manage_library_users, name='manage_library_users'),
    ]

if settings.FEATURES.get('ENABLE_EXPORT_GIT'):
    urlpatterns += [
        url(r'^export_git/{}$'.format(settings.COURSE_KEY_PATTERN),
            contentstore.views.export_git,
            name='export_git')
    ]

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns.append(url(r'^status/', include('openedx.core.djangoapps.service_status.urls')))

# The password pages in the admin tool are disabled so that all password
# changes go through our user portal and follow complexity requirements.
urlpatterns.append(url(r'^admin/password_change/$', handler404))
urlpatterns.append(url(r'^admin/auth/user/\d+/password/$', handler404))
urlpatterns.append(url(r'^admin/', include(admin.site.urls)))

# enable entrance exams
if settings.FEATURES.get('ENTRANCE_EXAMS'):
    urlpatterns.append(url(r'^course/{}/entrance_exam/?$'.format(settings.COURSE_KEY_PATTERN),
                       contentstore.views.entrance_exam))

# Enable Web/HTML Certificates
if settings.FEATURES.get('CERTIFICATES_HTML_VIEW'):
    from contentstore.views.certificates import (
        certificate_activation_handler,
        signatory_detail_handler,
        certificates_detail_handler,
        certificates_list_handler
    )

    urlpatterns += [
        url(r'^certificates/activation/{}/'.format(settings.COURSE_KEY_PATTERN),
            certificate_activation_handler,
            name='certificate_activation_handler'),
        url(r'^certificates/{}/(?P<certificate_id>\d+)/signatories/(?P<signatory_id>\d+)?$'.format(
            settings.COURSE_KEY_PATTERN), signatory_detail_handler, name='signatory_detail_handler'),
        url(r'^certificates/{}/(?P<certificate_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
            certificates_detail_handler, name='certificates_detail_handler'),
        url(r'^certificates/{}$'.format(settings.COURSE_KEY_PATTERN),
            certificates_list_handler, name='certificates_list_handler')
    ]

# Maintenance Dashboard
urlpatterns.append(url(r'^maintenance/', include('maintenance.urls', namespace='maintenance')))

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

    urlpatterns += static(
        settings.VIDEO_TRANSCRIPTS_SETTINGS['STORAGE_KWARGS']['base_url'],
        document_root=settings.VIDEO_TRANSCRIPTS_SETTINGS['STORAGE_KWARGS']['location']
    )

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))

# UX reference templates
urlpatterns.append(url(r'^template/(?P<template>.+)$', openedx.core.djangoapps.debug.views.show_reference_template,
                       name='openedx.core.djangoapps.debug.views.show_reference_template'))

# display error page templates, for testing purposes
urlpatterns += [
    url(r'^404$', handler404),
    url(r'^500$', handler500),
]

if settings.FEATURES.get('ENABLE_API_DOCS'):
    urlpatterns += [
        url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        url(r'^api-docs/$', schema_view.with_ui('swagger', cache_timeout=0)),
    ]

from openedx.core.djangoapps.plugins import constants as plugin_constants, plugin_urls
urlpatterns.extend(plugin_urls.get_patterns(plugin_constants.ProjectType.CMS))
