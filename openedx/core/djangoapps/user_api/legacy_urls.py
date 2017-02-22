"""
Defines the URL routes for this app.
"""

from django.conf import settings
from django.conf.urls import include, patterns, url
from rest_framework import routers

from . import views as user_api_views
from .models import UserPreference

USER_API_ROUTER = routers.DefaultRouter()
USER_API_ROUTER.register(r'users', user_api_views.UserViewSet)
USER_API_ROUTER.register(r'user_prefs', user_api_views.UserPreferenceViewSet)
urlpatterns = patterns(
    '',
    url(r'^v1/', include(USER_API_ROUTER.urls)),
    url(
        r'^v1/preferences/(?P<pref_key>{})/users/$'.format(UserPreference.KEY_REGEX),
        user_api_views.PreferenceUsersListView.as_view()
    ),
    url(
        r'^v1/forum_roles/(?P<name>[a-zA-Z]+)/users/$',
        user_api_views.ForumRoleUsersListView.as_view()
    ),

    url(
        r'^v1/preferences/email_opt_in/$',
        user_api_views.UpdateEmailOptInPreference.as_view(),
        name="preferences_email_opt_in"
    ),
    url(
        r'^v1/preferences/time_zones/$',
        user_api_views.CountryTimeZoneListView.as_view(),
    ),
)

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += patterns(
        '',
        url(r'^v1/account/login_session/$', user_api_views.LoginSessionView.as_view(),
            name="user_api_login_session"),
        url(r'^v1/account/registration/$', user_api_views.RegistrationView.as_view(),
            name="user_api_registration"),
        url(r'^v1/account/password_reset/$', user_api_views.PasswordResetView.as_view(),
            name="user_api_password_reset"),
    )
