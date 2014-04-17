"""
Courses API URI specification
The order of the URIs really matters here, due to the slash characters present in the identifiers
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('api_manager.courses_views',
                       url(r'/*$^', 'courses_list'),
                       url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/(?P<module_id>[a-zA-Z0-9/_:]+)/submodules/*$', 'modules_list'),
                       url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/(?P<module_id>[a-zA-Z0-9/_:]+)$', 'modules_detail'),
                       url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)/modules/*$', 'modules_list'),
                       url(r'^(?P<course_id>[a-zA-Z0-9/_:]+)$', 'courses_detail'),
                       )
