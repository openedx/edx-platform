"""
Courses API URI specification
The order of the URIs really matters here, due to the slash characters present in the identifiers
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'api_manager.courses_views',
    url(r'/*$^', 'courses_list'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/(?P<module_id>[a-zA-Z0-9/_:]+)/submodules/*$', 'modules_list'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/(?P<module_id>[a-zA-Z0-9/_:]+)$', 'modules_detail'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/*$', 'modules_list'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/groups/(?P<group_id>[0-9]+)$', 'courses_groups_detail'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/groups/*$', 'courses_groups_list'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/overview$', 'course_overview'),
    url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/updates$', 'course_updates'),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/static_tabs/(?P<tab_id>[a-zA-Z0-9/_:]+)$', 'static_tab_detail'),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/static_tabs$', 'static_tabs_list'),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)$', 'courses_detail'),
)
