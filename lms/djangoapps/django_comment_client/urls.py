"""
Urls for the django_comment_client.
"""
from django.conf.urls import url, patterns, include

urlpatterns = patterns(
    '',

    url(r'forum/?', include('django_comment_client.forum.urls')),
    url(r'', include('django_comment_client.base.urls')),
)
