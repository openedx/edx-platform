"""
URL mappings for the Survey feature
"""

from django.conf.urls import patterns, url


urlpatterns = patterns('survey.views',  # nopep8
    url(r'^survey_postback/$', 'survey_postback'),
)
