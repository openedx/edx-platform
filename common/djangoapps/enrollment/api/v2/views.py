from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import viewsets

from enrollment.api.v2 import serializers
from student.models import CourseEnrollment


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CourseEnrollmentSerializer
    queryset = CourseEnrollment.objects.all()

    def get_queryset(self):
        queryset = super(self, CourseEnrollmentViewSet).get_queryset()
        course_id = self.request.query_params.get('course_id', None)
        username = self.request.query_params.get('username', None)

        if course_id:
            try:
                course_id = CourseKey.from_string(course_id)
                queryset = queryset.filter(course_id=course_id)
            except InvalidKeyError:
                raise serializers.ValidationError(u'[{}] is not a valid course key.'.format(course_id))

        if username:
            queryset = queryset.filter(user__username=username)

        return queryset
