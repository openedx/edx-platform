from django.conf import settings
from django.conf.urls import url

from openedx.core.djangoapps.dashboard.views import CourseEnrollmentViewSet

from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(

    r'course-enrollments', CourseEnrollmentViewSet, 'course-enrollments'
)

urlpatterns = router.urls