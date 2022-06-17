"""
URLs for genplus core API v1.
"""
from django.conf.urls import url

from .views import (
    UserInfo,
    CharacterView,
    UserOnBoard
)

app_name = 'genplus_api_v1'

urlpatterns = [
    url(r'^userinfo/$', UserInfo.as_view()),
    url(r'^characters/$', CharacterView.as_view()),
    url(r'^onboard/$', UserOnBoard.as_view()),
]
