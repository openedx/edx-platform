"""
user manager API URLs
"""
from django.conf import settings
from django.conf.urls import include, url

from . import views

urlpatterns = [
    # Get list of all managers
    url(
        r'managers/$',
        views.ManagerListView.as_view(),
        name='manager-list',
    ),
    # Get or add direct reports of specified manager
    url(
        r'managers/{}/reports/$'.format(settings.USERNAME_PATTERN),
        views.ManagerReportsListView.as_view(),
        name='manager-direct-reports-list',
    ),
    # List managers for a specified user
    url(
        r'user/{}/managers/$'.format(settings.USERNAME_PATTERN),
        views.UserManagerListView.as_view(),
        name='user-managers-list',
    ),
]
