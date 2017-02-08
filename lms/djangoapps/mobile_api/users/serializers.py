"""
Serializer for user API
"""
from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers
from rest_framework.reverse import reverse

from certificates.api import certificate_downloadable_status
from courseware.access import has_access
from student.models import CourseEnrollment, User
from util.course import get_lms_link_for_about_page


class CourseOverviewField(serializers.RelatedField):
    """
    Custom field to wrap a CourseOverview object. Read-only.
    """

    def to_representation(self, course_overview):
        course_id = unicode(course_overview.id)
        request = self.context.get('request')
        return {
            # identifiers
            'id': course_id,
            'name': course_overview.display_name,
            'number': course_overview.display_number_with_default,
            'org': course_overview.display_org_with_default,

            # dates
            'start': course_overview.start,
            'start_display': course_overview.start_display,
            'start_type': course_overview.start_type,
            'end': course_overview.end,

            # notification info
            'subscription_id': course_overview.clean_id(padding_char='_'),

            # access info
            'courseware_access': has_access(
                request.user,
                'load_mobile',
                course_overview
            ).to_json(),

            # various URLs
            # course_image is sent in both new and old formats
            # (within media to be compatible with the new Course API)
            'media': {
                'course_image': {
                    'uri': course_overview.course_image_url,
                    'name': 'Course Image',
                }
            },
            'course_image': course_overview.course_image_url,
            'course_about': get_lms_link_for_about_page(CourseKey.from_string(course_id)),
            'course_updates': reverse(
                'course-updates-list',
                kwargs={'course_id': course_id},
                request=request,
            ),
            'course_handouts': reverse(
                'course-handouts-list',
                kwargs={'course_id': course_id},
                request=request,
            ),
            'discussion_url': reverse(
                'discussion_course',
                kwargs={'course_id': course_id},
                request=request,
            ) if course_overview.is_discussion_tab_enabled() else None,

            'video_outline': reverse(
                'video-summary-list',
                kwargs={'course_id': course_id},
                request=request,
            ),
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview", read_only=True)
    certificate = serializers.SerializerMethodField()

    def get_certificate(self, model):
        """Returns the information about the user's certificate in the course."""
        certificate_info = certificate_downloadable_status(model.user, model.course_id)
        if certificate_info['is_downloadable']:
            return {
                'url': self.context['request'].build_absolute_uri(
                    certificate_info['download_url']
                ),
            }
        else:
            return {}

    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course', 'certificate')
        lookup_field = 'username'


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializes User models
    """
    name = serializers.ReadOnlyField(source='profile.name')
    course_enrollments = serializers.HyperlinkedIdentityField(
        view_name='courseenrollment-detail',
        lookup_field='username'
    )

    class Meta(object):
        model = User
        fields = ('id', 'username', 'email', 'name', 'course_enrollments')
        lookup_field = 'username'
