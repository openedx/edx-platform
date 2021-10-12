"""
Views for course rating api.
"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend

from opaque_keys.edx.keys import CourseKey
from openedx.features.course_rating.api.v1.serializers import CourseRatingSerializer
from openedx.features.course_rating.models import CourseRating
from openedx.features.course_rating.permissions import CustomCourseRatingPermission


class CourseRatingViewSet(viewsets.ModelViewSet):
    """
    List, Create/Update CourseRating.
    """
    permission_classes = (CustomCourseRatingPermission,)
    serializer_class = CourseRatingSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['is_approved']

    def get_queryset(self):
        """
        Filter course ratings.
        """
        course_id = self.kwargs['course_id']
        course_key = CourseKey.from_string(course_id)
        return CourseRating.objects.filter(course=course_key)
