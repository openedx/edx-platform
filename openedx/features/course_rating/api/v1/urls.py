"""
Defines URLs for the course rating.
"""

from django.conf.urls import include, url
from rest_framework import routers

from openedx.features.course_rating.api.v1.views import CourseRatingViewSet, CourseAverageRatingAPIView

router = routers.DefaultRouter()
router.register(r'course_rating', CourseRatingViewSet, base_name='course_rating')

app_name = 'v1'

urlpatterns = [
    url(r'', include(router.urls)),
    url(r'course_average_rating/', CourseAverageRatingAPIView.as_view(), name='course_average_rating')
]
