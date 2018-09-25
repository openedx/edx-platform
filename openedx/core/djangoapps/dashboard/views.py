

from openedx.core.djangoapps.dashboard import serializers
from student.models import CourseEnrollment


from rest_framework import filters, viewsets


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """
    Viewset for routes related to Enterprise users.
    """
    queryset = CourseEnrollment.objects.all()
    serializer_class = serializers.CourseEnrollmentSerializer
