"""
Defines the URL routes for this app.
"""
from django.urls import path, re_path, include
from rest_framework import routers

from . import views as user_api_views
from .accounts.settings_views import account_settings
from .models import UserPreference

USER_API_ROUTER = routers.DefaultRouter()
USER_API_ROUTER.register(r'users', user_api_views.UserViewSet)
USER_API_ROUTER.register(r'user_prefs', user_api_views.UserPreferenceViewSet)

urlpatterns = [
    path('account/settings', account_settings, name='account_settings'),
    path('user_api/v1/', include(USER_API_ROUTER.urls)),
    re_path(
        fr'^user_api/v1/preferences/(?P<pref_key>{UserPreference.KEY_REGEX})/users/$',
        user_api_views.PreferenceUsersListView.as_view()
    ),
    re_path(
        r'^user_api/v1/forum_roles/(?P<name>[a-zA-Z]+)/users/$',
        user_api_views.ForumRoleUsersListView.as_view()
    ),

    path('user_api/v1/preferences/email_opt_in/', user_api_views.UpdateEmailOptInPreference.as_view(),
         name="preferences_email_opt_in_legacy"
         ),
    path('user_api/v1/preferences/time_zones/', user_api_views.CountryTimeZoneListView.as_view(),
         ),
]
