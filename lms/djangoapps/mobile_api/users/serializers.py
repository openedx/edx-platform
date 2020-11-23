"""
Serializer for user API
"""


import six
from rest_framework import serializers
from rest_framework.reverse import reverse

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.certificates.api import certificate_downloadable_status
from openedx.features.course_duration_limits.access import get_user_course_expiration_date
from common.djangoapps.student.models import CourseEnrollment, User
from common.djangoapps.util.course import get_encoded_course_sharing_utm_params, get_link_for_about_page


class CourseOverviewField(serializers.RelatedField):
    """
    Custom field to wrap a CourseOverview object. Read-only.
    """
    def to_representation(self, course_overview):
        course_id = six.text_type(course_overview.id)
        request = self.context.get('request')
        api_version = self.context.get('api_version')
        enrollment = CourseEnrollment.get_enrollment(user=self.context.get('request').user, course_key=course_id)

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
            'dynamic_upgrade_deadline': enrollment.upgrade_deadline,

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
            'course_about': get_link_for_about_page(course_overview),
            'course_sharing_utm_parameters': get_encoded_course_sharing_utm_params(),
            'course_updates': reverse(
                'course-updates-list',
                kwargs={'api_version': api_version, 'course_id': course_id},
                request=request,
            ),
            'course_handouts': reverse(
                'course-handouts-list',
                kwargs={'api_version': api_version, 'course_id': course_id},
                request=request,
            ),
            'discussion_url': reverse(
                'discussion_course',
                kwargs={'course_id': course_id},
                request=request,
            ) if course_overview.is_discussion_tab_enabled() else None,

            # This is an old API that was removed as part of DEPR-4. We keep the
            # field present in case API parsers expect it, but this API is now
            # removed.
            'video_outline': None,
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview", read_only=True)
    certificate = serializers.SerializerMethodField()
    audit_access_expires = serializers.SerializerMethodField()

    def get_audit_access_expires(self, model):
        """
        Returns expiration date for a course audit expiration, if any or null
        """
        return get_user_course_expiration_date(model.user, model.course)

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
        fields = ('audit_access_expires', 'created', 'mode', 'is_active', 'course', 'certificate')
        lookup_field = 'username'


class CourseEnrollmentSerializerv05(CourseEnrollmentSerializer):
    """
    Serializes CourseEnrollment models for v0.5 api
    Does not include 'audit_access_expires' field that is present in v1 api
    """
    class Meta(object):
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course', 'certificate')
        lookup_field = 'username'


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes User models
    """
    name = serializers.ReadOnlyField(source='profile.name')
    course_enrollments = serializers.SerializerMethodField()

    def get_course_enrollments(self, model):
        request = self.context.get('request')
        api_version = self.context.get('api_version')

        return reverse(
            'courseenrollment-detail',
            kwargs={'api_version': api_version, 'username': model.username},
            request=request
        )

    class Meta(object):
        model = User
        fields = ('id', 'username', 'email', 'name', 'course_enrollments')
        lookup_field = 'username'
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'mobile_api.User'
