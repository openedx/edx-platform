""" Users API URI specification """
from django.conf.urls import patterns, url

urlpatterns = patterns('api_manager.users_views',
                       url(r'/*$^', 'user_list'),
                       url(r'^(?P<user_id>[0-9]+)$', 'user_detail'),
                       url(r'^(?P<user_id>[0-9]+)/courses/*$', 'user_courses_list'),
                       url(r'^(?P<user_id>[0-9]+)/courses/(?P<course_id>[a-zA-Z0-9/_:]+)$', 'user_courses_detail'),
                       url(r'^(?P<user_id>[0-9]+)/groups/*$', 'user_groups_list'),
                       url(r'^(?P<user_id>[0-9]+)/groups/(?P<group_id>[0-9]+)$', 'user_groups_detail'),
                       )
