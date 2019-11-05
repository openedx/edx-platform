"""
Common URLs for User Authentication

Note: The split between urls.py and urls_common.py is hopefully temporary.
For now, this is needed because of difference in CMS and LMS that have
not yet been cleaned up.

"""
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import url

from .views import auto_auth, login, logout, password_reset, register


urlpatterns = [
    # Registration
    url(r'^create_account$', register.RegistrationView.as_view(), name='create_account'),
    url(r'^user_api/v1/account/registration/$', register.RegistrationView.as_view(),
        name="user_api_registration"),
    # Login
    url(r'^login_post$', login.login_user, name='login_post'),
    url(r'^login_ajax$', login.login_user, name="login"),
    url(r'^login_ajax/(?P<error>[^/]*)$', login.login_user),
    url(r'^user_api/v1/account/login_session/$', login.LoginSessionView.as_view(),
        name="user_api_login_session"),

    # Login Refresh of JWT Cookies
    url(r'^login_refresh$', login.login_refresh, name="login_refresh"),

    url(r'^logout$', logout.LogoutView.as_view(), name='logout'),

    url(r'^v1/account/password_reset/$', password_reset.PasswordResetView.as_view(),
        name="user_api_password_reset"),

]


# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += [
        url(r'^auto_auth$', auto_auth.auto_auth),
    ]
