"""
Defines the URL routes for this app.
"""

from django.conf.urls import patterns, url

from ..profile_images.views import ProfileImageView
from .accounts.views import AccountView
from .preferences.views import PreferencesView, PreferencesDetailView

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    '',
    url(
        r'^v1/accounts/{}$'.format(USERNAME_PATTERN),
        AccountView.as_view(),
        name="accounts_api"
    ),
    url(
        r'^v1/accounts/{}/image$'.format(USERNAME_PATTERN),
        ProfileImageView.as_view(),
        name="accounts_profile_image_api"
    ),
    url(
        r'^v1/preferences/{}$'.format(USERNAME_PATTERN),
        PreferencesView.as_view(),
        name="preferences_api"
    ),
    url(
        r'^v1/preferences/{}/(?P<preference_key>[a-zA-Z0-9_]+)$'.format(USERNAME_PATTERN),
        PreferencesDetailView.as_view(),
        name="preferences_detail_api"
    ),
)
