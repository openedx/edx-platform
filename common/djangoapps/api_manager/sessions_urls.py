""" Sessions API URI specification """
from django.conf.urls import patterns, url

urlpatterns = patterns('api_manager.sessions_views',
                       url(r'/*$^', 'session_list'),
                       url(r'^(?P<session_id>[a-z0-9]+)$', 'session_detail'),
                       )
