"""
Forum urls for the nodeBB discussion forum.
"""
from django.conf.urls import url, patterns

urlpatterns = patterns(
    'discussion_nodebb.views',
    url(r'', 'nodebb_form_discussion', name='nodebb_form_discussion'),
)
