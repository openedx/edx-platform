""" Groups API URI specification """
from django.conf.urls import patterns, url

urlpatterns = patterns('api_manager.groups_views',
                       url(r'/*$^', 'group_list'),
                       url(r'^(?P<group_id>[0-9]+)$', 'group_detail'),
                       url(r'^(?P<group_id>[0-9]+)/courses/*$', 'group_courses_list'),
                       url(r'^(?P<group_id>[0-9]+)/courses/(?P<course_id>[a-zA-Z0-9/_:]+)$', 'group_courses_detail'),
                       url(r'^(?P<group_id>[0-9]+)/users/*$', 'group_users_list'),
                       url(r'^(?P<group_id>[0-9]+)/users/(?P<user_id>[0-9]+)$', 'group_users_detail'),
                       url(r'^(?P<group_id>[0-9]+)/groups/*$', 'group_groups_list'),
                       url(r'^(?P<group_id>[0-9]+)/groups/(?P<related_group_id>[0-9]+)$', 'group_groups_detail'),
                       )
