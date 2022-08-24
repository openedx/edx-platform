"""
URLs for genplus learning API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProgramViewSet,
    ClassStudentViewSet,
)

lesson_viewset_router = DefaultRouter()
lesson_viewset_router.register('lessons', ProgramViewSet, basename='lessons')


app_name = 'genplus_learning_api_v1'

urlpatterns = [
    url(r'^lessons/unlock/(?P<pk>\d+)/$', ProgramViewSet.as_view({"put": "unlock_lesson"})),
    url(r'^class-students/(?P<group_id>\w+)/$', ClassStudentViewSet.as_view({'get': 'list'})),
    path('', include(lesson_viewset_router.urls)),
]
