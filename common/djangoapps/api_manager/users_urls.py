""" Users API URI specification """
from django.conf.urls import patterns, url

urlpatterns = patterns('api_manager.users_views',
                       url(r'/*$^', 'user_list'),
                       url(r'^(?P<user_id>[0-9]+)$', 'user_detail'),
                       url(r'^(?P<user_id>[0-9]+)/groups/*$', 'user_groups_list'),
                       url(r'^(?P<user_id>[0-9]+)/groups/(?P<group_id>[0-9]+)$', 'user_groups_detail'),
                       )
