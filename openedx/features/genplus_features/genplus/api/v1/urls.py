"""
URLs for genplus core API v1.
"""
from django.conf.urls import url

from .views import (
    UserInfo,
    CharacterView,
    StudentOnBoard
)

app_name = 'genplus_api_v1'

urlpatterns = [
    url(r'^userinfo/$', UserInfo.as_view()),
    url(r'^characters/$', CharacterView.as_view()),
    url(r'^onboard/$', StudentOnBoard.as_view()),
]
