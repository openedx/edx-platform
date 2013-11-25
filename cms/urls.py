from django.conf import settings
from django.conf.urls import patterns, include, url

# TODO: This should be removed once the CMS is running via wsgi on all production servers
import cms.startup as startup
from xmodule.modulestore import parsers
startup.run()

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

    url(r'^preview/xblock/(?P<usage_id>.*?)/handler/(?P<handler>[^/]*)(?:/(?P<suffix>[^/]*))?$',
        'contentstore.views.preview_handler', name='preview_handler'),

    # This is the URL to initially render the course advanced settings.
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/settings-advanced/(?P<name>[^/]+)$',
        'contentstore.views.course_config_advanced_page', name='course_advanced_settings'),
    # This is the URL used by BackBone for updating and re-fetching the model.
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/settings-advanced/(?P<name>[^/]+)/update.*$',
        'contentstore.views.course_advanced_updates', name='course_advanced_settings_updates'),

    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/textbooks/(?P<name>[^/]+)$',
        'contentstore.views.textbook_index', name='textbook_index'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/textbooks/(?P<name>[^/]+)/new$',
        'contentstore.views.create_textbook', name='create_textbook'),
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/textbooks/(?P<name>[^/]+)/(?P<tid>\d[^/]*)$',
        'contentstore.views.textbook_by_id', name='textbook_by_id'),

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
)

# User creation and updating views
urlpatterns += patterns(
    '',

    url(r'^create_account$', 'student.views.create_account'),
    url(r'^activate/(?P<key>[^/]*)$', 'student.views.activate_account', name='activate'),

    # ajax view that actually does the work
    url(r'^login_post$', 'student.views.login_user', name='login_post'),
    url(r'^logout$', 'student.views.logout_user', name='logout'),
)

# restful api
urlpatterns += patterns(
    'contentstore.views',

    url(r'^$', 'howitworks', name='homepage'),
    url(r'^howitworks$', 'howitworks'),
    url(r'^signup$', 'signup', name='signup'),
    url(r'^signin$', 'login_page', name='login'),
    url(r'^request_course_creator$', 'request_course_creator'),

    # (?ix) == ignore case and verbose (multiline regex)
    url(r'(?ix)^course_team/{}(/)?(?P<email>.+)?$'.format(parsers.URL_RE_SOURCE), 'course_team_handler'),
    url(r'(?ix)^course_info/{}$'.format(parsers.URL_RE_SOURCE), 'course_info_handler'),
    url(
        r'(?ix)^course_info_update/{}(/)?(?P<provided_id>\d+)?$'.format(parsers.URL_RE_SOURCE),
        'course_info_update_handler'
        ),
    url(r'(?ix)^course($|/){}$'.format(parsers.URL_RE_SOURCE), 'course_handler'),
    url(r'(?ix)^subsection($|/){}$'.format(parsers.URL_RE_SOURCE), 'subsection_handler'),
    url(r'(?ix)^unit($|/){}$'.format(parsers.URL_RE_SOURCE), 'unit_handler'),
    url(r'(?ix)^checklists/{}(/)?(?P<checklist_index>\d+)?$'.format(parsers.URL_RE_SOURCE), 'checklists_handler'),
    url(r'(?ix)^orphan/{}$'.format(parsers.URL_RE_SOURCE), 'orphan_handler'),
    url(r'(?ix)^assets/{}(/)?(?P<asset_id>.+)?$'.format(parsers.URL_RE_SOURCE), 'assets_handler'),
    url(r'(?ix)^import/{}$'.format(parsers.URL_RE_SOURCE), 'import_handler'),
    url(r'(?ix)^import_status/{}/(?P<filename>.+)$'.format(parsers.URL_RE_SOURCE), 'import_status_handler'),
    url(r'(?ix)^export/{}$'.format(parsers.URL_RE_SOURCE), 'export_handler'),
    url(r'(?ix)^xblock($|/){}$'.format(parsers.URL_RE_SOURCE), 'xblock_handler'),
    url(r'(?ix)^tabs/{}$'.format(parsers.URL_RE_SOURCE), 'tabs_handler'),
    url(r'(?ix)^settings/details/{}$'.format(parsers.URL_RE_SOURCE), 'settings_handler'),
    url(r'(?ix)^settings/grading/{}(/)?(?P<grader_index>\d+)?$'.format(parsers.URL_RE_SOURCE), 'grading_handler'),
)

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('cms',),
}

urlpatterns += patterns('',
    # Serve catalog of localized strings to be rendered by Javascript
    url(r'^i18n.js$', 'django.views.i18n.javascript_catalog', js_info_dict),
)

if settings.MITX_FEATURES.get('ENABLE_SERVICE_STATUS'):
    urlpatterns += patterns('',
        url(r'^status/', include('service_status.urls')),
    )

urlpatterns += patterns('', url(r'^admin/', include(admin.site.urls)),)

# enable automatic login
if settings.MITX_FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
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
#pylint: disable=C0103
handler404 = 'contentstore.views.render_404'
handler500 = 'contentstore.views.render_500'
