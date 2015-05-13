"""
Defines the URL routes for this app.
"""

from .accounts.views import AccountView
from .preferences.views import PreferencesView, PreferencesDetailView

from django.conf import settings
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^v1/accounts/' + settings.USERNAME_PATTERN + '$',
        AccountView.as_view(),
        name="accounts_api"
    ),
    url(
        r'^v1/preferences/' + settings.USERNAME_PATTERN + '$',
        PreferencesView.as_view(),
        name="preferences_api"
    ),
    url(
        r'^v1/preferences/' + settings.USERNAME_PATTERN + '/(?P<preference_key>[a-zA-Z0-9_]+)$',
        PreferencesDetailView.as_view(),
        name="preferences_detail_api"
    ),
)
