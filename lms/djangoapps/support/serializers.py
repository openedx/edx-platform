"""
Serializers for use in the support app.
"""


from rest_framework import serializers

from student.models import CourseEnrollment, ManualEnrollmentAudit
from lms.djangoapps.program_enrollments.models import (
    ProgramEnrollment,
    ProgramCourseEnrollment,
)

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

    class Meta(object):
        model = ProgramCourseEnrollment


class ProgramEnrollmentSerializer(serializers.Serializer):
    """ Serializes a Program Enrollment Model object """
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    modified = serializers.DateTimeField(format=DATETIME_FORMAT)
    external_user_key = serializers.CharField()
    status = serializers.CharField()
    program_uuid = serializers.UUIDField()
    program_course_enrollments = ProgramCourseEnrollmentSerializer(many=True)

    class Meta(object):
        model = ProgramEnrollment


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
