"""
URL mappings for the Survey feature
"""


from django.conf.urls import url

from lms.djangoapps.survey import views

urlpatterns = [
    url(r'^(?P<survey_name>[0-9A-Za-z]+)/$', views.view_survey, name='view_survey'),
    url(r'^(?P<survey_name>[0-9A-Za-z]+)/answers/$', views.submit_answers, name='submit_answers'),
]
