"""
    urls for the nodeBB discussion forum.
"""
from django.conf.urls import url, patterns

urlpatterns = patterns(
    'nodebb.views',
    url(r'', 'nodebb_forum_discussion', name='nodebb_forum_discussion'),
)
