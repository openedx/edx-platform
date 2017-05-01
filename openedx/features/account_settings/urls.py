"""
URLS for the new account settings page.
"""

from django.conf.urls import url

from views.account_settings import AccountSettingsView

urlpatterns = [
    url(
        r'^$',
        AccountSettingsView.as_view(),
        name='openedx.account.account_settings',
    ),
]
