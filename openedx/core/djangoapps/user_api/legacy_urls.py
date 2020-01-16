"""
Defines the URL routes for this app.
"""


from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers

from . import views as user_api_views
from .accounts.settings_views import account_settings
from .models import UserPreference

USER_API_ROUTER = routers.DefaultRouter()
USER_API_ROUTER.register(r'users', user_api_views.UserViewSet)
USER_API_ROUTER.register(r'user_prefs', user_api_views.UserPreferenceViewSet)

urlpatterns = [
    url(r'^account/settings$', account_settings, name='account_settings'),
    url(r'^user_api/v1/', include(USER_API_ROUTER.urls)),
    url(
        r'^user_api/v1/preferences/(?P<pref_key>{})/users/$'.format(UserPreference.KEY_REGEX),
        user_api_views.PreferenceUsersListView.as_view()
    ),
    url(
        r'^user_api/v1/forum_roles/(?P<name>[a-zA-Z]+)/users/$',
        user_api_views.ForumRoleUsersListView.as_view()
    ),

    url(
        r'^user_api/v1/preferences/email_opt_in/$',
        user_api_views.UpdateEmailOptInPreference.as_view(),
        name="preferences_email_opt_in"
    ),
    url(
        r'^user_api/v1/preferences/time_zones/$',
        user_api_views.CountryTimeZoneListView.as_view(),
    ),
]
