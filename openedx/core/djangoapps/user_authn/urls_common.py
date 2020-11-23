"""
Common URLs for User Authentication

Note: The split between urls.py and urls_common.py is hopefully temporary.
For now, this is needed because of difference in CMS and LMS that have
not yet been cleaned up.

This is also home to urls for endpoints that have been consolidated from other djangoapps,
which leads to inconsistent prefixing.

"""


from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.views import PasswordResetCompleteView

from .views import auto_auth, login, logout, password_reset, register
from .views.password_reset import PasswordResetConfirmWrapper

urlpatterns = [
    # Registration
    url(r'^create_account$', register.RegistrationView.as_view(), name='create_account'),

    # Moved from user_api/legacy_urls.py
    # `user_api` prefix is preserved for backwards compatibility.
    url(r'^user_api/v1/account/registration/$', register.RegistrationView.as_view(),
        name="user_api_registration"),

    # Moved from user_api/urls.py
    # `api/user` prefix is preserved for backwards compatibility.
    url(
        r'^api/user/v1/validation/registration$',
        register.RegistrationValidationView.as_view(),
        name='registration_validation'
    ),

    url(r'^login_ajax$', login.login_user, name="login_api"),

    # Moved from user_api/legacy_urls.py
    # `user_api` prefix is preserved for backwards compatibility.
    url(r'^user_api/v1/account/login_session/$', login.LoginSessionView.as_view(),
        name="user_api_login_session"),

    # Login Refresh of JWT Cookies
    url(r'^login_refresh$', login.login_refresh, name="login_refresh"),

    url(r'^logout$', logout.LogoutView.as_view(), name='logout'),

    # Moved from user_api/legacy_urls.py
    url(r'^user_api/v1/account/password_reset/$', password_reset.PasswordResetView.as_view(),
        name="user_api_password_reset"),

    # Password reset api views.
    url(r'^password_reset/$', password_reset.password_reset, name='password_reset'),
    url(
        r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        PasswordResetConfirmWrapper.as_view(),
        name='password_reset_confirm',
    ),
    url(r'^account/password$', password_reset.password_change_request_handler, name='password_change_request'),

]

# password reset django views (see above for password reset views)
urlpatterns += [
    url(
        r'^password_reset_complete/$',
        PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]

# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += [
        url(r'^auto_auth$', auto_auth.auto_auth),
    ]
