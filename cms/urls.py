"""
Urls of Studio.
"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.admin import autodiscover as django_autodiscover
from django.utils.translation import ugettext_lazy as _
from edx_api_doc_tools import make_docs_urls
from ratelimitbackend import admin

import openedx.core.djangoapps.common_views.xblock
import openedx.core.djangoapps.debug.views
import openedx.core.djangoapps.lang_pref.views
from cms.djangoapps.contentstore import views as contentstore_views
from cms.djangoapps.contentstore.views.organization import OrganizationListView
from openedx.core.apidocs import api_info
from openedx.core.djangoapps.password_policy import compliance as password_policy_compliance
from openedx.core.djangoapps.password_policy.forms import PasswordPolicyAwareAdminAuthForm
from openedx.core import toggles as core_toggles


django_autodiscover()
admin.site.site_header = _('Studio Administration')
admin.site.site_title = admin.site.site_header

if password_policy_compliance.should_enforce_compliance_on_login():
    admin.site.login_form = PasswordPolicyAwareAdminAuthForm

# Custom error pages
# These are used by Django to render these error codes. Do not remove.
# pylint: disable=invalid-name
handler404 = contentstore_views.render_404
handler500 = contentstore_views.render_500

# Pattern to match a course key or a library key
COURSELIKE_KEY_PATTERN = r'(?P<course_key_string>({}|{}))'.format(
    r'[^/]+/[^/]+/[^/]+', r'[^/:]+:[^/+]+\+[^/+]+(\+[^/]+)?'
)

# Pattern to match a library key only
LIBRARY_KEY_PATTERN = r'(?P<library_key_string>library-v1:[^/+]+\+[^/+]+)'

urlpatterns = [
    url(r'', include('openedx.core.djangoapps.user_authn.urls_common')),
    url(r'', include('common.djangoapps.student.urls')),
    url(r'^transcripts/upload$', contentstore_views.upload_transcripts, name='upload_transcripts'),
    url(r'^transcripts/download$', contentstore_views.download_transcripts, name='download_transcripts'),
    url(r'^transcripts/check$', contentstore_views.check_transcripts, name='check_transcripts'),
    url(r'^transcripts/choose$', contentstore_views.choose_transcripts, name='choose_transcripts'),
    url(r'^transcripts/replace$', contentstore_views.replace_transcripts, name='replace_transcripts'),
    url(r'^transcripts/rename$', contentstore_views.rename_transcripts, name='rename_transcripts'),
    url(r'^preview/xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        contentstore_views.preview_handler, name='preview_handler'),
    url(r'^xblock/(?P<usage_key_string>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>.*))?$',
        contentstore_views.component_handler, name='component_handler'),
    url(r'^xblock/resource/(?P<block_type>[^/]*)/(?P<uri>.*)$',
        openedx.core.djangoapps.common_views.xblock.xblock_resource, name='xblock_resource_url'),
    url(r'', include('openedx.core.djangoapps.xblock.rest_api.urls', namespace='xblock_api')),
    url(r'^not_found$', contentstore_views.not_found, name='not_found'),
    url(r'^server_error$', contentstore_views.server_error, name='server_error'),
    url(r'^organizations$', OrganizationListView.as_view(), name='organizations'),

    # noop to squelch ajax errors
    url(r'^event$', contentstore_views.event, name='event'),
    url(r'^heartbeat', include('openedx.core.djangoapps.heartbeat.urls')),
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
    url(r'^$', contentstore_views.howitworks, name='homepage'),
    url(r'^howitworks$', contentstore_views.howitworks, name='howitworks'),
    url(r'^signin_redirect_to_lms$', contentstore_views.login_redirect_to_lms, name='login_redirect_to_lms'),
    url(r'^request_course_creator$', contentstore_views.request_course_creator, name='request_course_creator'),
    url(r'^course_team/{}(?:/(?P<email>.+))?$'.format(COURSELIKE_KEY_PATTERN),
        contentstore_views.course_team_handler, name='course_team_handler'),
    url(r'^course_info/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.course_info_handler,
        name='course_info_handler'),
    url(r'^course_info_update/{}/(?P<provided_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.course_info_update_handler, name='course_info_update_handler'
        ),
    url(r'^home/?$', contentstore_views.course_listing, name='home'),
    url(r'^course/{}/search_reindex?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.course_search_index_handler,
        name='course_search_index_handler'
        ),
    url(r'^course/{}?$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.course_handler, name='course_handler'),

    url(r'^checklists/{}?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.checklists_handler,
        name='checklists_handler'),

    url(r'^course_notifications/{}/(?P<action_state_id>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.course_notifications_handler,
        name='course_notifications_handler'),
    url(r'^course_rerun/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.course_rerun_handler,
        name='course_rerun_handler'),
    url(r'^container/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore_views.container_handler,
        name='container_handler'),
    url(r'^orphan/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.orphan_handler,
        name='orphan_handler'),
    url(r'^assets/{}/{}?$'.format(settings.COURSE_KEY_PATTERN, settings.ASSET_KEY_PATTERN),
        contentstore_views.assets_handler,
        name='assets_handler'),
    url(r'^import/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore_views.import_handler,
        name='import_handler'),
    url(r'^import_status/{}/(?P<filename>.+)$'.format(COURSELIKE_KEY_PATTERN),
        contentstore_views.import_status_handler, name='import_status_handler'),
    # rest api for course import/export
    url(r'^api/courses/',
        include('cms.djangoapps.contentstore.api.urls', namespace='courses_api')
        ),
    url(r'^export/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore_views.export_handler,
        name='export_handler'),
    url(r'^export_output/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore_views.export_output_handler,
        name='export_output_handler'),
    url(r'^export_status/{}$'.format(COURSELIKE_KEY_PATTERN), contentstore_views.export_status_handler,
        name='export_status_handler'),
    url(r'^xblock/outline/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore_views.xblock_outline_handler,
        name='xblock_outline_handler'),
    url(r'^xblock/container/{}$'.format(settings.USAGE_KEY_PATTERN), contentstore_views.xblock_container_handler,
        name='xblock_container_handler'),
    url(r'^xblock/{}/(?P<view_name>[^/]+)$'.format(settings.USAGE_KEY_PATTERN), contentstore_views.xblock_view_handler,
        name='xblock_view_handler'),
    url(r'^xblock/{}?$'.format(settings.USAGE_KEY_PATTERN), contentstore_views.xblock_handler,
        name='xblock_handler'),
    url(r'^tabs/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.tabs_handler,
        name='tabs_handler'),
    url(r'^settings/details/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.settings_handler,
        name='settings_handler'),
    url(r'^settings/grading/{}(/)?(?P<grader_index>\d+)?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.grading_handler, name='grading_handler'),
    url(r'^settings/advanced/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.advanced_settings_handler,
        name='advanced_settings_handler'),
    url(r'^textbooks/{}$'.format(settings.COURSE_KEY_PATTERN), contentstore_views.textbooks_list_handler,
        name='textbooks_list_handler'),
    url(r'^textbooks/{}/(?P<textbook_id>\d[^/]*)$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.textbooks_detail_handler, name='textbooks_detail_handler'),
    url(r'^videos/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.videos_handler, name='videos_handler'),
    url(r'^generate_video_upload_link/{}'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.generate_video_upload_link_handler, name='generate_video_upload_link'),
    url(r'^video_images/{}(?:/(?P<edx_video_id>[-\w]+))?$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.video_images_handler, name='video_images_handler'),
    url(r'^transcript_preferences/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.transcript_preferences_handler, name='transcript_preferences_handler'),
    url(r'^transcript_credentials/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.transcript_credentials_handler, name='transcript_credentials_handler'),
    url(r'^transcript_download/$', contentstore_views.transcript_download_handler, name='transcript_download_handler'),
    url(r'^transcript_upload/$', contentstore_views.transcript_upload_handler, name='transcript_upload_handler'),
    url(r'^transcript_delete/{}(?:/(?P<edx_video_id>[-\w]+))?(?:/(?P<language_code>[^/]*))?$'.format(
        settings.COURSE_KEY_PATTERN
    ), contentstore_views.transcript_delete_handler, name='transcript_delete_handler'),
    url(r'^video_encodings_download/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.video_encodings_download, name='video_encodings_download'),
    url(r'^group_configurations/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore_views.group_configurations_list_handler,
        name='group_configurations_list_handler'),
    url(r'^group_configurations/{}/(?P<group_configuration_id>\d+)(/)?(?P<group_id>\d+)?$'.format(
        settings.COURSE_KEY_PATTERN), contentstore_views.group_configurations_detail_handler,
        name='group_configurations_detail_handler'),
    url(r'^api/val/v0/', include('edxval.urls')),
    url(r'^api/tasks/v0/', include('user_tasks.urls')),
    url(r'^accessibility$', contentstore_views.accessibility, name='accessibility'),
]

if not settings.DISABLE_DEPRECATED_SIGNIN_URL:
    # TODO: Remove deprecated signin url when traffic proves it is no longer in use
    urlpatterns += [
        url(r'^signin$', contentstore_views.login_redirect_to_lms),
    ]

if not settings.DISABLE_DEPRECATED_SIGNUP_URL:
    # TODO: Remove deprecated signup url when traffic proves it is no longer in use
    urlpatterns += [
        url(r'^signup$', contentstore_views.register_redirect_to_lms, name='register_redirect_to_lms'),
    ]

JS_INFO_DICT = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

urlpatterns += [
    url(r'^openassessment/fileupload/', include('openassessment.fileupload.urls')),
]

if settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES'):
    urlpatterns += [
        url(r'^library/{}?$'.format(LIBRARY_KEY_PATTERN),
            contentstore_views.library_handler, name='library_handler'),
        url(r'^library/{}/team/$'.format(LIBRARY_KEY_PATTERN),
            contentstore_views.manage_library_users, name='manage_library_users'),
    ]

if settings.FEATURES.get('ENABLE_EXPORT_GIT'):
    urlpatterns += [
        url(r'^export_git/{}$'.format(settings.COURSE_KEY_PATTERN),
            contentstore_views.export_git,
            name='export_git')
    ]

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns.append(url(r'^status/', include('openedx.core.djangoapps.service_status.urls')))

# The password pages in the admin tool are disabled so that all password
# changes go through our user portal and follow complexity requirements.
if not settings.FEATURES.get('ENABLE_CHANGE_USER_PASSWORD_ADMIN'):
    urlpatterns.append(url(r'^admin/auth/user/\d+/password/$', handler404))
urlpatterns.append(url(r'^admin/password_change/$', handler404))
urlpatterns.append(url(r'^admin/', admin.site.urls))

# enable entrance exams
if core_toggles.ENTRANCE_EXAMS.is_enabled():
    urlpatterns.append(url(r'^course/{}/entrance_exam/?$'.format(settings.COURSE_KEY_PATTERN),
                       contentstore_views.entrance_exam))

# Enable Web/HTML Certificates
if settings.FEATURES.get('CERTIFICATES_HTML_VIEW'):
    from cms.djangoapps.contentstore.views.certificates import (
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
urlpatterns.append(url(r'^maintenance/', include('cms.djangoapps.maintenance.urls', namespace='maintenance')))

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

urlpatterns.append(
    url(
        r'^api/learning_sequences/',
        include(
            ('openedx.core.djangoapps.content.learning_sequences.urls', 'learning_sequences'),
            namespace='learning_sequences'
        ),
    ),
)

# display error page templates, for testing purposes
urlpatterns += [
    url(r'^404$', handler404),
    url(r'^500$', handler500),
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

# pylint: disable=wrong-import-position, wrong-import-order
from edx_django_utils.plugins import get_plugin_url_patterns  # isort:skip
# pylint: disable=wrong-import-position
from openedx.core.djangoapps.plugins.constants import ProjectType  # isort:skip
urlpatterns.extend(get_plugin_url_patterns(ProjectType.CMS))

# Contentstore
urlpatterns += [
    url(r'^api/contentstore/', include('cms.djangoapps.contentstore.rest_api.urls'))
]
