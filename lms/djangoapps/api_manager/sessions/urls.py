""" Sessions API URI specification """
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.sessions import views as sessions_views

urlpatterns = patterns(
    '',
    url(r'/*$^', sessions_views.SessionsList.as_view()),
    url(r'^(?P<session_id>[a-z0-9]+)$', sessions_views.SessionsDetail.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
