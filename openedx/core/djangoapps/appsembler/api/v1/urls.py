"""URL definitions for Tahoe API version 1
"""

from django.conf.urls import include, url
from rest_framework import routers

# Initially doing relative pathing because the full path is a mouthful and a half:
#  `openedx.core.djangoapps.appsembler.api`

from openedx.core.djangoapps.appsembler.api.v1 import views


router = routers.DefaultRouter()

router.register(
    r'courses',
    views.CourseViewSet,
    'courses',
)

router.register(
    r'enrollments',
    views.EnrollmentViewSet,
    'enrollments',
)

router.register(
    r'registrations',
    views.RegistrationViewSet,
    'registrations',
)

router.register(
    r'users',
    views.UserIndexViewSet,
    'users',
)

urlpatterns = [
    url(r'', include(router.urls, )),
]
