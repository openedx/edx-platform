""" URL configuration for the third party auth API """


from django.conf import settings

from .views import ThirdPartyAuthUserStatusView, UserMappingView, UserView, UserViewV2
from django.urls import path, re_path

PROVIDER_PATTERN = r'(?P<provider_id>[\w.+-]+)(?:\:(?P<idp_slug>[\w.+-]+))?'

urlpatterns = [
    re_path(
        fr'^v0/users/{settings.USERNAME_PATTERN}$',
        UserView.as_view(),
        name='third_party_auth_users_api',
    ),
    path('v0/users/', UserViewV2.as_view(), name='third_party_auth_users_api_v2'),
    re_path(
        fr'^v0/providers/{PROVIDER_PATTERN}/users$',
        UserMappingView.as_view(),
        name='third_party_auth_user_mapping_api',
    ),
    path(
        'v0/providers/user_status', ThirdPartyAuthUserStatusView.as_view(),
        name='third_party_auth_user_status_api',
    ),
]
