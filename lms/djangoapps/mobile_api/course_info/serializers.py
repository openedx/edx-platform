"""
Course Info serializers
"""
from rest_framework import serializers

from common.djangoapps.util.milestones_helpers import (
    get_pre_requisite_courses_not_completed,
)
from lms.djangoapps.courseware.access import administrative_accesses_to_course_for_user
from lms.djangoapps.courseware.access_utils import check_course_open_for_learner
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class CourseInfoOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for additional course fields that should be returned in BlocksInfoInCourseView.
    """

    name = serializers.CharField(source='display_name')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    is_self_paced = serializers.BooleanField(source='self_paced')
    media = serializers.SerializerMethodField()

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
        )

    @staticmethod
    def get_media(obj):
        return {'image': obj.image_urls}


class CourseAccessSerializer(serializers.Serializer):
    """
    Get info whether a user should be able to view course material.
    """

    hasUnmetPrerequisites = serializers.SerializerMethodField(method_name="get_has_unmet_prerequisites")
    isTooEarly = serializers.SerializerMethodField(method_name="get_is_too_early")
    isStaff = serializers.SerializerMethodField(method_name="get_is_staff")

    def get_has_unmet_prerequisites(self, data: dict) -> bool:
        """
        Check whether or not a course has unmet prerequisites.
        """
        return any(get_pre_requisite_courses_not_completed(data.get("user"), [data.get("course_id")]))

    def get_is_too_early(self, data: dict) -> bool:
        """
        Determine if the course is open to a learner (course has started or user has early beta access).
        """
        return not check_course_open_for_learner(data.get("user"), data.get("course"))

    def get_is_staff(self, data: dict) -> bool:
        """
        Determine whether a user has staff access to this course.
        """
        return any(administrative_accesses_to_course_for_user(data.get("user"), data.get("course_id")))
