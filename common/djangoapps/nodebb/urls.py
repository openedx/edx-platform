"""
    urls for the nodeBB discussion forum.
"""
from django.conf.urls import url

from .views import nodebb_forum_discussion

urlpatterns = [
    url(r'', nodebb_forum_discussion, name='nodebb_forum_discussion'),
]
