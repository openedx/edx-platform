"""
Defines the URL routes for this app.
"""


from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import TeamsDashboardView

urlpatterns = [
    url(r"^$", login_required(TeamsDashboardView.as_view()), name="teams_dashboard")
]
