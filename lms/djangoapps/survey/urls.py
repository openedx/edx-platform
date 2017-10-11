"""
URL mappings for the Survey feature
"""

from django.conf.urls import url

from survey.views import view_survey, submit_answers

urlpatterns = [
    url(r'^(?P<survey_name>[0-9A-Za-z]+)/$', view_survey, name='view_survey'),
    url(r'^(?P<survey_name>[0-9A-Za-z]+)/answers/$', submit_answers, name='submit_answers'),
]
