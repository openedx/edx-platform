"""
The urls for on-boarding app.
"""
from django.conf.urls import url

from oef import views

urlpatterns = [
    url(r"^$", views.fetch_survey, name="oef_survey"),
    url(r"^answer", views.save_answer, name="oef_survey")
]
