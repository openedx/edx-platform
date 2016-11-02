""" URL configuration for the third party auth API """

from django.conf.urls import patterns, url

from .views import UserView, UserMappingView

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'
PROVIDER_PATTERN = r'(?P<provider_id>[\w.+-]+)(?:\:(?P<idp_slug>[\w.+-]+))?'

urlpatterns = patterns(
    '',
    url(r'^v0/users/' + USERNAME_PATTERN + '$', UserView.as_view(), name='third_party_auth_users_api'),
    url(r'^v0/providers/' + PROVIDER_PATTERN + '/users$', UserMappingView.as_view(),
        name='third_party_auth_user_mapping_api'),
)
