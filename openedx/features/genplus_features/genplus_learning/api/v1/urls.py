"""
URLs for genplus learning API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LessonViewSet
)

lesson_viewset_router = DefaultRouter()
lesson_viewset_router.register('lessons', LessonViewSet, basename='lessons')


app_name = 'genplus_learning_api_v1'

urlpatterns = [
    path('', include(lesson_viewset_router.urls)),
]
