"""
URLs for genplus core API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    UserInfo,
    CharacterViewSet
)

app_name = 'genplus_api_v1'

character_viewset_router = DefaultRouter()
character_viewset_router.register('characters', CharacterViewSet, basename='characters')

urlpatterns = [
    url(r'^userinfo/$', UserInfo.as_view()),
    url(r'^characters/select/(?P<pk>\d+)/$', CharacterViewSet.as_view({"post": "select_character"})),
    path('', include(character_viewset_router.urls)),
]
