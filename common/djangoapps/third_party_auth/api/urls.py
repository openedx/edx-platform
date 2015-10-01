""" URL configuration for the third party auth API """

from django.conf.urls import patterns, url

from .views import UserView

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    '',
    url(r'^v0/users/' + USERNAME_PATTERN + '$', UserView.as_view(), name='third_party_auth_users_api'),
)
