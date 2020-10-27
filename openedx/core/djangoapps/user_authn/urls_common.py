"""
Common URLs for User Authentication

Note: The split between urls.py and urls_common.py is hopefully temporary.
For now, this is needed because of difference in CMS and LMS that have
not yet been cleaned up.

"""
from django.conf import settings
from django.conf.urls import url

from .views import auto_auth, login, logout, deprecated


urlpatterns = [
    url(r'^create_account$', deprecated.create_account, name='create_account'),
    url(r'^login_post$', login.login_user, name='login_post'),
    url(r'^login_ajax$', login.login_user, name="login"),
    url(r'^login_ajax/(?P<error>[^/]*)$', login.login_user),
    url(r'^login_refresh$', login.login_refresh, name="login_refresh"),

    url(r'^logout$', logout.LogoutView.as_view(), name='logout'),
]


# enable automatic login
if settings.FEATURES.get('AUTOMATIC_AUTH_FOR_TESTING'):
    urlpatterns += [
        url(r'^auto_auth$', auto_auth.auto_auth),
    ]
