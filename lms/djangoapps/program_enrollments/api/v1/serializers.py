"""
API Serializers
"""
from __future__ import absolute_import

from rest_framework import serializers
from six import text_type

from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.api.v1.constants import (
    CourseRunProgressStatuses,
    ProgramEnrollmentResponseStatuses
)


class InvalidStatusMixin(object):
    """
    Mixin to provide has_invalid_status method
    """
    def has_invalid_status(self):
        """
        Returns whether or not this serializer has an invalid error choice on the "status" field
        """
        try:
            for status_error in self.errors['status']:
                if status_error.code == 'invalid_choice':
                    return True
        except KeyError:
            pass
        return False


# pylint: disable=abstract-method
class ProgramEnrollmentSerializer(serializers.ModelSerializer, InvalidStatusMixin):
    """
    Serializer for Program Enrollments
    """

    class Meta(object):
        model = ProgramEnrollment
        fields = ('user', 'external_user_key', 'program_uuid', 'curriculum_uuid', 'status')
        validators = []

    def validate(self, attrs):
        """ This modifies self.instance in the case of updates """
        if not self.instance:
            enrollment = ProgramEnrollment(**attrs)
            enrollment.full_clean()
        else:
            for key, value in attrs.items():
                setattr(self.instance, key, value)
            self.instance.full_clean()

        return attrs

    def create(self, validated_data):
        return ProgramEnrollment.objects.create(**validated_data)


class BaseProgramEnrollmentRequestMixin(serializers.Serializer, InvalidStatusMixin):
    """
    Base fields for all program enrollment related serializers
    """
    student_key = serializers.CharField()
    status = serializers.ChoiceField(
        allow_blank=False,
        choices=ProgramEnrollmentResponseStatuses.VALID_STATUSES
    )


class ProgramEnrollmentCreateRequestSerializer(BaseProgramEnrollmentRequestMixin):
    """
    Serializer for program enrollment creation requests
    """
    curriculum_uuid = serializers.UUIDField()


class ProgramEnrollmentModifyRequestSerializer(BaseProgramEnrollmentRequestMixin):
    """
    Serializer for program enrollment modification requests
    """
    pass


class ProgramEnrollmentListSerializer(serializers.Serializer):
    """
    Serializer for listing enrollments in a program.
    """
    student_key = serializers.CharField(source='external_user_key')
    status = serializers.CharField()
    account_exists = serializers.SerializerMethodField()
    curriculum_uuid = serializers.UUIDField()

    class Meta(object):
        model = ProgramEnrollment

    def get_account_exists(self, obj):
        return bool(obj.user)


# pylint: disable=abstract-method
class ProgramCourseEnrollmentRequestSerializer(serializers.Serializer, InvalidStatusMixin):
    """
    Serializer for request to create a ProgramCourseEnrollment
    """
    STATUS_CHOICES = ['active', 'inactive']

    student_key = serializers.CharField(allow_blank=False)
    status = serializers.ChoiceField(allow_blank=False, choices=STATUS_CHOICES)


class ProgramCourseEnrollmentListSerializer(serializers.Serializer):
    """
    Serializer for listing course enrollments in a program.
    """
    student_key = serializers.SerializerMethodField()
    status = serializers.CharField()
    account_exists = serializers.SerializerMethodField()
    curriculum_uuid = serializers.SerializerMethodField()

    class Meta(object):
        model = ProgramCourseEnrollment

    def get_student_key(self, obj):
        return obj.program_enrollment.external_user_key

    def get_account_exists(self, obj):
        return bool(obj.program_enrollment.user)

    def get_curriculum_uuid(self, obj):
        return text_type(obj.program_enrollment.curriculum_uuid)


class ProgramCourseGradeResult(object):
    """
    Represents a courserun grade for a user enrolled through a program.

    Can be passed to ProgramCourseGradeResultSerializer.
    """
    is_error = False

    def __init__(self, program_course_enrollment, course_grade):
        """
        Creates a new grade result given a ProgramCourseEnrollment object
        and a course grade object.
        """
        self.student_key = program_course_enrollment.program_enrollment.external_user_key
        self.passed = course_grade.passed
        self.percent = course_grade.percent
        self.letter_grade = course_grade.letter_grade


class ProgramCourseGradeErrorResult(object):
    """
    Represents a failure to load a courserun grade for a user enrolled through
    a program.

    Can be passed to ProgramCourseGradeResultSerializer.
    """
    is_error = True

    def __init__(self, program_course_enrollment, exception=None):
        """
        Creates a new course grade error object given a
        ProgramCourseEnrollment and an exception.
        """
        self.student_key = program_course_enrollment.program_enrollment.external_user_key
        self.error = text_type(exception) if exception else u"Unknown error"


class ProgramCourseGradeResultSerializer(serializers.Serializer):
    """
    Serializer for a user's grade in a program courserun.

    Meant to be used with ProgramCourseGradeResult
    or ProgramCourseGradeErrorResult as input.
    Absence of fields other than `student_key` will be ignored.
    """
    # Required
    student_key = serializers.CharField()

    # From ProgramCourseGradeResult only
    passed = serializers.BooleanField(required=False)
    percent = serializers.FloatField(required=False)
    letter_grade = serializers.CharField(required=False)

    # From ProgramCourseGradeErrorResult only
    error = serializers.CharField(required=False)


class DueDateSerializer(serializers.Serializer):
    """
    Serializer for a due date.
    """
    name = serializers.CharField()
    url = serializers.CharField()
    date = serializers.DateTimeField()


class CourseRunOverviewSerializer(serializers.Serializer):
    """
    Serializer for a course run overview.
    """
    STATUS_CHOICES = [
        CourseRunProgressStatuses.IN_PROGRESS,
        CourseRunProgressStatuses.UPCOMING,
        CourseRunProgressStatuses.COMPLETED
    ]

    course_run_id = serializers.CharField()
    display_name = serializers.CharField()
    resume_course_run_url = serializers.CharField(required=False)
    course_run_url = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    course_run_status = serializers.ChoiceField(allow_blank=False, choices=STATUS_CHOICES)
    emails_enabled = serializers.BooleanField(required=False)
    due_dates = serializers.ListField(child=DueDateSerializer())
    micromasters_title = serializers.CharField(required=False)
    certificate_download_url = serializers.CharField(required=False)


class CourseRunOverviewListSerializer(serializers.Serializer):
    """
    Serializer for a list of course run overviews.
    """
    course_runs = serializers.ListField(child=CourseRunOverviewSerializer())
