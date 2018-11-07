"""
Urls for the django_comment_client.
"""
from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    '',

    url(r'', include('django_comment_client.base.urls')),
)
