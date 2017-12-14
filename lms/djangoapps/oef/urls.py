"""
The urls for on-boarding app.
"""
from django.conf.urls import url

from oef import views

urlpatterns = [
    url(r"^$", views.fetch_survey, name="oef_survey"),
    url(r"^(?P<user_survey_id>[0-9]+)$", views.get_survey_by_id, name="oef_survey_by_id"),
    url(r"^answer", views.save_answer, name="oef_survey_answer"),
    url(r"^instructions", views.oef_instructions, name="oef_instructions"),
    url(r"^dashboard", views.oef_dashboard, name="oef_dashboard")
]
