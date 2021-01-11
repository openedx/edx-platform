"""
Serializers for use in the support app.
"""
import json

from django.urls import reverse

from rest_framework import serializers

from common.djangoapps.student.models import CourseEnrollment, ManualEnrollmentAudit
from lms.djangoapps.program_enrollments.models import (
    ProgramEnrollment,
    ProgramCourseEnrollment,
)
from openedx.core.djangoapps.catalog.utils import get_programs_by_uuids
from openedx.features.course_experience import default_course_url_name

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
# pylint: disable=abstract-method


class ManualEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes a manual enrollment audit object."""
    enrolled_by = serializers.SlugRelatedField(slug_field='email', read_only=True, default='')

    class Meta(object):
        model = ManualEnrollmentAudit
        fields = ('enrolled_by', 'time_stamp', 'reason')


class CourseEnrollmentSerializer(serializers.Serializer):
    """ Serializers a student_courseenrollment model object """
    course_id = serializers.CharField()
    is_active = serializers.BooleanField()
    mode = serializers.CharField()

    class Meta(object):
        model = CourseEnrollment


class ProgramCourseEnrollmentSerializer(serializers.Serializer):
    """ Serializes a Program Course Enrollment model object """
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    modified = serializers.DateTimeField(format=DATETIME_FORMAT)
    status = serializers.CharField()
    course_key = serializers.CharField()
    course_enrollment = CourseEnrollmentSerializer()
    course_url = serializers.SerializerMethodField()

    class Meta(object):
        model = ProgramCourseEnrollment

    def get_course_url(self, obj):
        course_url_name = default_course_url_name(obj.course_key)
        return reverse(course_url_name, kwargs={'course_id': obj.course_key})


class ProgramEnrollmentSerializer(serializers.Serializer):
    """ Serializes a Program Enrollment Model object """
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    modified = serializers.DateTimeField(format=DATETIME_FORMAT)
    external_user_key = serializers.CharField()
    status = serializers.CharField()
    program_uuid = serializers.UUIDField()
    program_course_enrollments = ProgramCourseEnrollmentSerializer(many=True)
    program_name = serializers.SerializerMethodField()

    class Meta(object):
        model = ProgramEnrollment

    def get_program_name(self, obj):
        program_list = get_programs_by_uuids([obj.program_uuid])
        return next(iter(program_list), {}).get('title', '')


def serialize_user_info(user, user_social_auths=None):
    """
    Helper method to serialize resulting in user_info_object
    based on passed in django models
    """
    user_info = {
        'username': user.username,
        'email': user.email,
    }
    if user_social_auths:
        for user_social_auth in user_social_auths:
            user_info.setdefault('sso_list', []).append({
                'uid': user_social_auth.uid,
            })
    return user_info


def serialize_sso_records(user_social_auths):
    """
    Serialize user social auth model object
    """
    sso_records = []
    for user_social_auth in user_social_auths:
        sso_records.append({
            'provider': user_social_auth.provider,
            'uid': user_social_auth.uid,
            'created': user_social_auth.created,
            'modified': user_social_auth.modified,
            'extraData': json.dumps(user_social_auth.extra_data),
        })
    return sso_records
