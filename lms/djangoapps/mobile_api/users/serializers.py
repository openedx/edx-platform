"""
Serializer for user API
"""
from rest_framework import serializers
from rest_framework.reverse import reverse

from courseware.courses import course_image_url
from student.models import CourseEnrollment, User
from certificates.models import certificate_status_for_student, CertificateStatuses


class CourseOverviewField(serializers.RelatedField):
    """Custom field to wrap a CourseDescriptor object. Read-only."""

    def to_native(self, course_overview):
        course_id = unicode(course_overview.id)
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
        else:
            video_outline_url = None
            course_updates_url = None
            course_handouts_url = None

        return {
            "id": course_id,
            "name": course_overview.display_name,
            "number": course_overview.display_number_with_default,
            "org": course_overview.display_org_with_default,
            "start": course_overview.start,
            "end": course_overview.end,
            "course_image": course_overview.course_image_url,
            "social_urls": {
                "facebook": course_overview.facebook_url,
            },
            "latest_updates": {
                "video": None
            },
            "video_outline": video_outline_url,
            "course_updates": course_updates_url,
            "course_handouts": course_handouts_url,
            "subscription_id": course_overview.clean_id(padding_char='_'),
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview")
    certificate = serializers.SerializerMethodField('get_certificate')

    def get_certificate(self, model):
        """Returns the information about the user's certificate in the course."""
        certificate_info = certificate_status_for_student(model.user, model.course_id)
        if certificate_info['status'] == CertificateStatuses.downloadable:
            return {
                "url": certificate_info['download_url'],
            }
        else:
            return {}

    class Meta(object):  # pylint: disable=missing-docstring
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course', 'certificate')
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

    class Meta(object):  # pylint: disable=missing-docstring
        model = User
        fields = ('id', 'username', 'email', 'name', 'course_enrollments')
        lookup_field = 'username'
