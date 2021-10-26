"""
Views for course rating api.
"""
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend

import organizations
from opaque_keys.edx.keys import CourseKey

from openedx.features.course_rating.api.v1.serializers import (
    CourseAverageRatingListSerializer,
    CourseRatingSerializer,
)
from openedx.features.course_rating.models import CourseRating, CourseAverageRating
from openedx.features.course_rating.permissions import CustomCourseRatingPermission
from openedx.features.edly.models import EdlySubOrganization


class CourseRatingViewSet(viewsets.ModelViewSet):
    """
    List, Create/Update CourseRating.
    """
    permission_classes = (CustomCourseRatingPermission,)
    serializer_class = CourseRatingSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['is_approved', 'user']

    def get_queryset(self):
        """
        Filter course ratings.
        """
        course_id = self.kwargs['course_id']
        course_key = CourseKey.from_string(course_id)
        return CourseRating.objects.filter(course=course_key)


class CourseAverageRatingAPIView(ListAPIView):
    """
    List CourseAverageRating.
    """
    serializer_class = CourseAverageRatingListSerializer
    model = CourseAverageRating

    def get_queryset(self):
        edx_orgs = EdlySubOrganization.objects.filter(
            lms_site=self.request.site
        ).values_list('edx_organizations', flat=True)

        course_ids = organizations.models.OrganizationCourse.objects.filter(
            organization__in=edx_orgs
        ).values_list('course_id', flat=True)

        return CourseAverageRating.objects.filter(course__in=course_ids)
