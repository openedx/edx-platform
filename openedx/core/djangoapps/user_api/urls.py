"""
Defines the URL routes for this app.
"""

from .accounts.views import AccountView
from .profiles.views import ProfileView

from django.conf.urls import patterns, url

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    '',
    url(
        r'^v0/accounts/' + USERNAME_PATTERN + '$',
        AccountView.as_view(),
        name="accounts_api"
    ),
    url(
        r'^v0/profiles/' + USERNAME_PATTERN + '$',
        ProfileView.as_view(),
        name="profiles_api"
    ),
)
