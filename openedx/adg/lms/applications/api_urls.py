"""
All urls for applications APIs
"""
from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import EducationViewSet, WorkExperienceViewSet

router = DefaultRouter()
router.register('education', EducationViewSet, basename='education')
router.register('work_experience', WorkExperienceViewSet, basename='work_experience')

app_name = 'applications'
urlpatterns = [
    path('', include(router.urls)),
]
