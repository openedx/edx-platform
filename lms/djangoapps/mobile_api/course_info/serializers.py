"""
Course Info serializers
"""
from rest_framework import serializers
from typing import Union

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.course import get_encoded_course_sharing_utm_params, get_link_for_about_page
from common.djangoapps.util.milestones_helpers import (
    get_pre_requisite_courses_not_completed,
)
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.access import administrative_accesses_to_course_for_user
from lms.djangoapps.courseware.access_utils import check_course_open_for_learner
from lms.djangoapps.mobile_api.users.serializers import ModeSerializer
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_duration_limits.access import get_user_course_expiration_date


class CourseInfoOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for additional course fields that should be returned in BlocksInfoInCourseView.
    """

    name = serializers.CharField(source='display_name')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    is_self_paced = serializers.BooleanField(source='self_paced')
    media = serializers.SerializerMethodField()
    course_sharing_utm_parameters = serializers.SerializerMethodField()
    course_about = serializers.SerializerMethodField('get_course_about_url')
    course_modes = serializers.SerializerMethodField()

    class Meta:
        model = CourseOverview
        fields = (
            'name',
            'number',
            'org',
            'start',
            'start_display',
            'start_type',
            'end',
            'is_self_paced',
            'media',
            'course_sharing_utm_parameters',
            'course_about',
            'course_modes',
        )

    @staticmethod
    def get_media(obj):
        """
        Return course images in the correct format.
        """
        return {'image': obj.image_urls}

    def get_course_sharing_utm_parameters(self, obj):
        return get_encoded_course_sharing_utm_params()

    def get_course_about_url(self, course_overview):
        return get_link_for_about_page(course_overview)

    def get_course_modes(self, course_overview):
        """
        Retrieve course modes associated with the course.
        """
        course_modes = CourseMode.modes_for_course(
            course_overview.id,
            only_selectable=False
        )
        return [
            ModeSerializer(mode).data
            for mode in course_modes
        ]


class MobileCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the CourseEnrollment object used in the BlocksInfoInCourseView.
    """

    class Meta:
        fields = ('created', 'mode', 'is_active', 'upgrade_deadline')
        model = CourseEnrollment
        lookup_field = 'username'


class CourseAccessSerializer(serializers.Serializer):
    """
    Get info whether a user should be able to view course material.
    """

    has_unmet_prerequisites = serializers.SerializerMethodField(method_name='get_has_unmet_prerequisites')
    is_too_early = serializers.SerializerMethodField(method_name='get_is_too_early')
    is_staff = serializers.SerializerMethodField(method_name='get_is_staff')
    audit_access_expires = serializers.SerializerMethodField()
    courseware_access = serializers.SerializerMethodField()

    def get_has_unmet_prerequisites(self, data: dict) -> bool:
        """
        Check whether or not a course has unmet prerequisites.
        """
        return any(get_pre_requisite_courses_not_completed(data.get('user'), [data.get('course_id')]))

    def get_is_too_early(self, data: dict) -> bool:
        """
        Determine if the course is open to a learner (course has started or user has early beta access).
        """
        return not check_course_open_for_learner(data.get('user'), data.get('course'))

    def get_is_staff(self, data: dict) -> bool:
        """
        Determine whether a user has staff access to this course.
        """
        return any(administrative_accesses_to_course_for_user(data.get('user'), data.get('course_id')))

    def get_audit_access_expires(self, data: dict) -> Union[str, None]:
        """
        Returns expiration date for a course audit expiration, if any or null
        """
        return get_user_course_expiration_date(data.get('user'), data.get('course'))

    def get_courseware_access(self, data: dict) -> dict:
        """
        Determine if the learner has access to the course, otherwise show error message.
        """
        return has_access(data.get('user'), 'load_mobile', data.get('course')).to_json()
