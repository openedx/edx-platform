"""
Defines URLs for the course rating.
"""

from django.conf.urls import include, url
from rest_framework import routers
from django.conf import settings

from openedx.features.course_rating.api.v1.views import CourseRatingViewSet

router = routers.DefaultRouter()
router.register(r'course_rating/{}'.format(settings.COURSE_ID_PATTERN), CourseRatingViewSet, base_name='course_rating')

app_name = 'v1'

urlpatterns = [
    url(r'', include(router.urls)),
]
