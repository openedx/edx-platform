"""
URLs for the V1 of the Learner Dashboard API.
"""
from django.conf.urls import url

from .views import ProgramListView

app_name = 'v1'
urlpatterns = [
    url(
        r'^programs/$',
        ProgramListView.as_view(),
        name='program_listing'
    ),
]
