"""
Serializer for user API
"""
from rest_framework import serializers
from rest_framework.reverse import reverse

from courseware.courses import course_image_url
from student.models import CourseEnrollment, User


class CourseField(serializers.RelatedField):
    """Custom field to wrap a CourseDescriptor object. Read-only."""

    def to_native(self, course):
        course_id = unicode(course.id)
        request = self.context.get('request', None)
        if request:
            video_outline_url = reverse(
                'video-summary-list',
                kwargs={'course_id': course_id},
                request=request
            )
            course_updates_url = reverse(
                'course-updates-list',
                kwargs={'course_id': course_id},
                request=request
            )
            course_handouts_url = reverse(
                'course-handouts-list',
                kwargs={'course_id': course_id},
                request=request
            )
            course_about_url = reverse(
                'course-about-detail',
                kwargs={'course_id': course_id},
                request=request
            )
        else:
            video_outline_url = None
            course_updates_url = None
            course_handouts_url = None
            course_about_url = None

        return {
            "id": course_id,
            "name": course.display_name,
            "number": course.number,
            "org": course.display_org_with_default,
            "start": course.start,
            "end": course.end,
            "course_image": course_image_url(course),
            "latest_updates": {
                "video": None
            },
            "video_outline": video_outline_url,
            "course_updates": course_updates_url,
            "course_handouts": course_handouts_url,
            "course_about": course_about_url,
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseField()

    class Meta:  # pylint: disable=C0111
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course')
        lookup_field = 'username'


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes User models
    """
    name = serializers.Field(source='profile.name')
    course_enrollments = serializers.HyperlinkedIdentityField(
        view_name='courseenrollment-detail',
        lookup_field='username'
    )

    class Meta:  # pylint: disable=C0111
        model = User
        fields = ('id', 'username', 'email', 'name', 'course_enrollments')
        lookup_field = 'username'
