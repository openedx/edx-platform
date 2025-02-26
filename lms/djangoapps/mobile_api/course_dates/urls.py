"""
URLs for course_dates API
"""

from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AllCourseDatesViewSet

router = DefaultRouter()
router.register(rf"^{settings.USERNAME_PATTERN}", AllCourseDatesViewSet, basename="course-dates")

urlpatterns = [
    path("", include(router.urls)),
]
