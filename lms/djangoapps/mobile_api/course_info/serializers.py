"""
Serializer for course_info API
"""


from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.course_api.serializers import CourseDetailSerializer


class CourseInfoDetailSerializer(CourseDetailSerializer):
    """
        Serializer for Course objects providing additional details about the
        course.

        This serializer returns more data - 'is_enrolled' user's status.
    """
    def to_representation(self, instance):
        response = super().to_representation(instance)

        if self.context['request'].user.is_authenticated:
            response['is_enrolled'] = CourseEnrollment.is_enrolled(self.context['request'].user, instance.id)
        return response
