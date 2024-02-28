"""
Logistration API urls
"""

from django.conf.urls import url

from openedx.core.djangoapps.user_authn.api.views import TPAContextView, CookieRefreshView

urlpatterns = [
    url(
        r'^third_party_auth_context$', TPAContextView.as_view(), name='third_party_auth_context'
    ),
    url(r'^cookie/refresh/', CookieRefreshView.as_view(), name='cookie_refresh_view'),
]
