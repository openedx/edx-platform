"""URL definitions for Tahoe API version 2
"""

from django.urls import include, path
from rest_framework import routers

from openedx.core.djangoapps.appsembler.api.v1 import views
from openedx.core.djangoapps.appsembler.api.v2 import views as views_v2


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
    views_v2.RegistrationViewSet,
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
