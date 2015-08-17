"""
Defines the URL routes for this app.
"""

from .accounts.views import AccountView
from .preferences.views import PreferencesView, PreferencesDetailView

from django.conf.urls import patterns, url

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    '',
    url(
        r'^v1/accounts/' + USERNAME_PATTERN + '$',
        AccountView.as_view(),
        name="accounts_api"
    ),
    url(
        r'^v1/preferences/' + USERNAME_PATTERN + '$',
        PreferencesView.as_view(),
        name="preferences_api"
    ),
    url(
        r'^v1/preferences/' + USERNAME_PATTERN + '/(?P<preference_key>[a-zA-Z0-9_]+)$',
        PreferencesDetailView.as_view(),
        name="preferences_detail_api"
    ),
)
