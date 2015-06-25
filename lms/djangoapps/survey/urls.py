"""
URL mappings for the Survey feature
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    'survey.views',

    url(r'^(?P<survey_name>[0-9A-Za-z]+)/$', 'view_survey', name='view_survey'),
    url(r'^(?P<survey_name>[0-9A-Za-z]+)/answers/$', 'submit_answers', name='submit_answers'),
)
