"""
Defines the URL routes for this app.
"""
from django.contrib.auth.decorators import login_required

from .views import TeamsDashboardView
from django.urls import path

urlpatterns = [
    path('', login_required(TeamsDashboardView.as_view()), name="teams_dashboard")
]
