"""
All the urls for our_team app
"""
from django.urls import path

from .views import OurTeamView

urlpatterns = [
    path('', OurTeamView.as_view(), name='our_team'),
]
