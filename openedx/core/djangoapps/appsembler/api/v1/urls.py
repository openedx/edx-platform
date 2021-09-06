"""URL definitions for Tahoe API version 1
"""

from django.urls import include, path
from rest_framework import routers

# Initially doing relative pathing because the full path is a mouthful and a half:
#  `openedx.core.djangoapps.appsembler.api`

from openedx.core.djangoapps.appsembler.api.v1 import views


router = routers.DefaultRouter()

router.register(
    r'courses',
    views.CourseViewSet,
    basename='courses',
)

router.register(
    r'enrollments',
    views.EnrollmentViewSet,
    basename='enrollments',
)

router.register(
    r'registrations',
    views.RegistrationViewSet,
    basename='registrations',
)

router.register(
    r'users',
    views.UserIndexViewSet,
    basename='users'
)

urlpatterns = [
    path('', include(router.urls)),
]
