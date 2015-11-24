"""
Serializer for user API
"""
from rest_framework import serializers
from rest_framework.reverse import reverse

from django.template import defaultfilters

from courseware.access import has_access
from student.models import CourseEnrollment, User
from certificates.models import certificate_status_for_student, CertificateStatuses
from xmodule.course_module import DEFAULT_START_DATE


class CourseOverviewField(serializers.RelatedField):
    """
    Custom field to wrap a CourseOverview object. Read-only.
    """

    def to_representation(self, course_overview):
        course_id = unicode(course_overview.id)

        if course_overview.advertised_start is not None:
            start_type = 'string'
            start_display = course_overview.advertised_start
        elif course_overview.start != DEFAULT_START_DATE:
            start_type = 'timestamp'
            start_display = defaultfilters.date(course_overview.start, 'DATE_FORMAT')
        else:
            start_type = 'empty'
            start_display = None

        request = self.context.get('request')
        return {
            # identifiers
            'id': course_id,
            'name': course_overview.display_name,
            'number': course_overview.display_number_with_default,
            'org': course_overview.display_org_with_default,

            # dates
            'start': course_overview.start,
            'start_display': start_display,
            'start_type': start_type,
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
            'course_image': course_overview.course_image_url,
            'course_about': reverse(
                'about_course',
                kwargs={'course_id': course_id},
                request=request,
            ),
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

            # Note: The following 2 should be deprecated.
            'social_urls': {
                'facebook': course_overview.facebook_url,
            },
            'latest_updates': {
                'video': None
            },
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models
    """
    course = CourseOverviewField(source="course_overview", read_only=True)
    certificate = serializers.SerializerMethodField()

    def get_certificate(self, model):
        """Returns the information about the user's certificate in the course."""
        certificate_info = certificate_status_for_student(model.user, model.course_id)
        if certificate_info['status'] == CertificateStatuses.downloadable:
            return {
                "url": certificate_info['download_url'],
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
