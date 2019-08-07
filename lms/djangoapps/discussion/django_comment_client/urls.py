"""
Urls for the django_comment_client.
"""
from __future__ import absolute_import

from django.conf.urls import include, url

urlpatterns = [
    url(r'', include('lms.djangoapps.discussion.django_comment_client.base.urls')),
]
