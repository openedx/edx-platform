"""
The urls for on-boarding app.
"""
from django.conf.urls import patterns, url

from oef import views



urlpatterns = [
    url(r"^$", views.fetch_survey, name="oef_survey"),
    url(r"^topic/(?P<topic_id>[0-9]+)", views.get_survey_topic, name="oef_survey"),
]
