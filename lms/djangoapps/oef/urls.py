"""
The urls for on-boarding app.
"""
from django.conf.urls import patterns, url

from onboarding_survey import views


urlpatterns = [
    url(r"^recommendations/$", views.recommendations, name="recommendations"),

]
