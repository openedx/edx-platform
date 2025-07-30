"""
Course API Serializers.  Representing course catalog data
"""

from rest_framework import serializers

from lms.djangoapps.course_home_api.progress.serializers import CertificateDataSerializer
from lms.djangoapps.course_home_api.outline.serializers import CourseGoalsSerializer
from openedx.core.lib.api.fields import AbsoluteURLField


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

    class Meta:
        ref_name = 'courseware_api'

    def get_uri(self, course_overview):
        """
        Get the representation for the media resource's URI
        """
        return getattr(course_overview, self.uri_attribute)


class ImageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Collection of URLs pointing to images of various sizes.

    The URLs will be absolute URLs with the host set to the host of the current request. If the values to be
    serialized are already absolute URLs, they will be unchanged.
    """
    raw = AbsoluteURLField()
    small = AbsoluteURLField()
    large = AbsoluteURLField()

    class Meta:
        ref_name = 'courseware_api'


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')
    course_video = _MediaSerializer(source='*', uri_attribute='course_video_url')
    image = ImageSerializer(source='image_urls')

    class Meta:
        ref_name = 'courseware_api'


class CourseProgramSerializer(serializers.Serializer):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    progress = serializers.SerializerMethodField()
    slug = serializers.CharField()
    title = serializers.CharField()
    url = AbsoluteURLField()
    uuid = serializers.UUIDField()

    def get_progress(self, program):
        progress = program['progress']
        return {
            'completed': progress['completed'],
            'in_progress': progress['in_progress'],
            'not_started': progress['not_started']
        }


class CourseInfoSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

    access_expiration = serializers.DictField()
    content_type_gating_enabled = serializers.BooleanField()
    course_goals = CourseGoalsSerializer()
    effort = serializers.CharField()
    end = serializers.DateTimeField()
    enrollment = serializers.DictField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()
    entrance_exam_data = serializers.DictField()
    id = serializers.CharField()  # pylint: disable=invalid-name
    license = serializers.CharField()
    language = serializers.CharField(allow_null=True)
    media = _CourseApiMediaCollectionSerializer(source='*')
    name = serializers.CharField(source='display_name_with_default_escaped')
    offer = serializers.DictField()
    related_programs = CourseProgramSerializer(many=True)
    short_description = serializers.CharField()
    start = serializers.DateTimeField()
    start_display = serializers.CharField()
    start_type = serializers.CharField()
    pacing = serializers.CharField()
    user_timezone = serializers.CharField()
    show_calculator = serializers.BooleanField()
    can_access_proctored_exams = serializers.BooleanField()
    notes = serializers.DictField()
    marketing_url = serializers.CharField()
    celebrations = serializers.DictField()
    user_has_passing_grade = serializers.BooleanField()
    course_exit_page_is_active = serializers.BooleanField()
    certificate_data = CertificateDataSerializer()
    verify_identity_url = AbsoluteURLField()
    verification_status = serializers.CharField()
    linkedin_add_to_profile_url = serializers.URLField()
    is_integrity_signature_enabled = serializers.BooleanField()
    user_needs_integrity_signature = serializers.BooleanField()
    learning_assistant_enabled = serializers.BooleanField()

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        If `requested_fields` is set, then only return that subset of fields.
        """
        super().__init__(*args, **kwargs)
        requested_fields = self.context['requested_fields']
        if requested_fields is not None:
            allowed = set(requested_fields.split(','))
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
