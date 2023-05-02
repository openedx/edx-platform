"""
Views for the notifications API.
"""
from rest_framework import generics, permissions
from common.djangoapps.student.models import CourseEnrollment
from .serializers import CourseEnrollmentSerializer


class CourseEnrollmentListView(generics.ListAPIView):
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return CourseEnrollment.objects.filter(user=user, is_active=True)

