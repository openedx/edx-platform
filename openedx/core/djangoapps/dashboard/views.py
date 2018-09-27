
from datetime import date

from openedx.core.djangoapps.dashboard import serializers
from student.models import CourseEnrollment


from rest_framework import filters, viewsets


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise users.
    """
    serializer_class = serializers.CourseEnrollmentSerializer

    def get_queryset(self):
        queryset = CourseEnrollment.objects.all().select_related('course')
        archived = self.request.query_params.get('archived')

        if archived == 'true':
            queryset = queryset.filter(course__end__lte=date.today())
        elif archived == 'false':
            queryset = queryset.filter(course__end__gte=date.today())
        return queryset
