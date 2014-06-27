from django.conf import settings
from django.conf.urls import patterns, include, url

# There is a course creators admin table.
from ratelimitbackend import admin
admin.autodiscover()

urlpatterns = patterns('',  # nopep8

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
        'contentstore.views.xblock.xblock_resource', name='xblock_resource_url'),

    # temporary landing page for a course
    url(r'^edge/(?P<org>[^/]+)/(?P<course>[^/]+)/course/(?P<coursename>[^/]+)$',
        'contentstore.views.landing', name='landing'),

    url(r'^not_found$', 'contentstore.views.not_found', name='not_found'),
    url(r'^server_error$', 'contentstore.views.server_error', name='server_error'),

    # temporary landing page for edge
    url(r'^edge$', 'contentstore.views.edge', name='edge'),
    # noop to squelch ajax errors
    url(r'^event$', 'contentstore.views.event', name='event'),

    url(r'^xmodule/', include('pipeline_js.urls')),
    url(r'^heartbeat$', include('heartbeat.urls')),

    url(r'^user_api/', include('user_api.urls')),
    url(r'^lang_pref/', include('lang_pref.urls')),
)

# User creation and updating views
urlpatterns += patterns(
    '',

    url(r'^create_account$', 'student.views.create_account', name='create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account', name='activate'),

    # ajax view that actually does the work
    url(r'^login_post$', 'student.views.login_user', name='login_post'),
    url(r'^logout$', 'student.views.logout_user', name='logout'),
    url(r'^embargo$', 'student.views.embargo', name="embargo"),
)

# restful api
urlpatterns += patterns(
    'contentstore.views',

    url(r'^$', 'howitworks', name='homepage'),
    url(r'^howitworks$', 'howitworks'),
    url(r'^signup$', 'signup', name='signup'),
    url(r'^signin$', 'login_page', name='login'),
    url(r'^request_course_creator$', 'request_course_creator'),

    url(r'^course_team/(?P<course_key_string>[^/]+)/(?P<email>.+)?$', 'course_team_handler'),
    url(r'^course_info/(?P<course_key_string>[^/]+)$', 'course_info_handler'),
    url(
        r'^course_info_update/(?P<course_key_string>[^/]+)/(?P<provided_id>\d+)?$',
        'course_info_update_handler'
    ),
    url(r'^course/(?P<course_key_string>[^/]+)?$', 'course_handler', name='course_handler'),
    url(r'^subsection/(?P<usage_key_string>[^/]+)$', 'subsection_handler'),
    url(r'^unit/(?P<usage_key_string>[^/]+)$', 'unit_handler'),
    url(r'^container/(?P<usage_key_string>[^/]+)$', 'container_handler'),
    url(r'^checklists/(?P<course_key_string>[^/]+)/(?P<checklist_index>\d+)?$', 'checklists_handler'),
    url(r'^orphan/(?P<course_key_string>[^/]+)$', 'orphan_handler'),
    url(r'^assets/(?P<course_key_string>[^/]+)/(?P<asset_key_string>.+)?$', 'assets_handler'),
    url(r'^import/(?P<course_key_string>[^/]+)$', 'import_handler'),
    url(r'^import_status/(?P<course_key_string>[^/]+)/(?P<filename>.+)$', 'import_status_handler'),
    url(r'^export/(?P<course_key_string>[^/]+)$', 'export_handler'),
    url(r'^xblock/(?P<usage_key_string>[^/]+)/(?P<view_name>[^/]+)$', 'xblock_view_handler'),
    url(r'^xblock/(?P<usage_key_string>[^/]+)?$', 'xblock_handler'),
    url(r'^tabs/(?P<course_key_string>[^/]+)$', 'tabs_handler'),
    url(r'^settings/details/(?P<course_key_string>[^/]+)$', 'settings_handler'),
    url(r'^settings/grading/(?P<course_key_string>[^/]+)(/)?(?P<grader_index>\d+)?$', 'grading_handler'),
    url(r'^settings/advanced/(?P<course_key_string>[^/]+)$', 'advanced_settings_handler'),
    url(r'^textbooks/(?P<course_key_string>[^/]+)$', 'textbooks_list_handler'),
    url(r'^textbooks/(?P<course_key_string>[^/]+)/(?P<textbook_id>\d[^/]*)$', 'textbooks_detail_handler'),
)

if settings.FEATURES.get('ENABLE_GROUP_CONFIGURATIONS'):
    urlpatterns += (url(r'^group_configurations/(?P<course_key_string>[^/]+)$',
                        'contentstore.views.group_configurations_list_handler'),)

js_info_dict = {
    'domain': 'djangojs',
    # We need to explicitly include external Django apps that are not in LOCALE_PATHS.
    'packages': ('openassessment',),
}

urlpatterns += patterns('',
    # Serve catalog of localized strings to be rendered by Javascript
    url(r'^i18n.js$', 'django.views.i18n.javascript_catalog', js_info_dict),
)


if settings.FEATURES.get('ENABLE_EXPORT_GIT'):
    urlpatterns += (url(r'^export_git/(?P<course_key_string>[^/]+)$',
                        'contentstore.views.export_git', name='export_git'),)

if settings.FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += patterns('',
        url(r'^status/', include('service_status.urls')),
    )

if settings.FEATURES.get('AUTH_USE_CAS'):
    urlpatterns += (
        url(r'^cas-auth/login/$', 'external_auth.views.cas_login', name="cas-login"),
        url(r'^cas-auth/logout/$', 'django_cas.views.logout', {'next_page': '/'}, name="cas-logout"),
    )

urlpatterns += patterns('', url(r'^admin/', include(admin.site.urls)),)

# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += (
        url(r'^auto_auth$', 'student.views.auto_auth'),
    )

if settings.DEBUG:
    try:
        from .urls_dev import urlpatterns as dev_urlpatterns
        urlpatterns += dev_urlpatterns
    except ImportError:
        pass

# Custom error pages
# pylint: disable=C0103
handler404 = 'contentstore.views.render_404'
handler500 = 'contentstore.views.render_500'

# display error page templates, for testing purposes
urlpatterns += (
    url(r'404', handler404),
    url(r'500', handler500),
)
