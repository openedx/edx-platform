"""
Course API Serializers.  Representing course catalog data
"""


import six.moves.urllib.error  # pylint: disable=import-error
import six.moves.urllib.parse  # pylint: disable=import-error
import six.moves.urllib.request  # pylint: disable=import-error
from django.urls import reverse
from rest_framework import serializers

from lms.djangoapps.courseware.tabs import get_course_tab_list
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.api.fields import AbsoluteURLField
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

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


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')
    course_video = _MediaSerializer(source='*', uri_attribute='course_video_url')
    image = ImageSerializer(source='image_urls')


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

    blocks_url = serializers.SerializerMethodField()
    effort = serializers.CharField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()
    id = serializers.CharField()  # pylint: disable=invalid-name
    media = _CourseApiMediaCollectionSerializer(source='*')
    name = serializers.CharField(source='display_name_with_default_escaped')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    short_description = serializers.CharField()
    start = serializers.DateTimeField()
    start_display = serializers.CharField()
    start_type = serializers.CharField()
    pacing = serializers.CharField()
    mobile_available = serializers.BooleanField()
    hidden = serializers.SerializerMethodField()
    invitation_only = serializers.BooleanField()

    # 'course_id' is a deprecated field, please use 'id' instead.
    course_id = serializers.CharField(source='id', read_only=True)

    def get_hidden(self, course_overview):
        """
        Get the representation for SerializerMethodField `hidden`
        Represents whether course is hidden in LMS
        """
        catalog_visibility = course_overview.catalog_visibility
        return catalog_visibility in ['about', 'none']

    def get_blocks_url(self, course_overview):
        """
        Get the representation for SerializerMethodField `blocks_url`
        """
        base_url = '?'.join([
            reverse('blocks_in_course'),
            six.moves.urllib.parse.urlencode({'course_id': course_overview.id}),
        ])
        return self.context['request'].build_absolute_uri(base_url)


class CourseDetailSerializer(CourseSerializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing additional details about the
    course.

    This serializer makes additional database accesses (to the modulestore) and
    returns more data (including 'overview' text). Therefore, for performance
    and bandwidth reasons, it is expected that this serializer is used only
    when serializing a single course, and not for serializing a list of
    courses.
    """

    overview = serializers.SerializerMethodField()

    def get_overview(self, course_overview):
        """
        Get the representation for SerializerMethodField `overview`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        return CourseDetails.fetch_about_attribute(course_overview.id, 'overview')


class CourseWithTabsSerializer(CourseSerializer):
    enrollment = serializers.SerializerMethodField()
    tabs = serializers.SerializerMethodField()

    # these deprecated fields have been removed
    course_id = None
    blocks_url = None

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        If `requested_fields` is set, then only return that subset of fields.
        """
        super().__init__(*args, **kwargs)
        self.user = self.context['user']
        requested_fields = self.context['requested_fields']
        if requested_fields is not None:
            allowed = set(requested_fields.split(','))
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def get_tabs(self, course_overview):
        """
        Return course tab metadata.
        """
        # Ideally, we wouldn't have to load the course, but get_course_tabs won't work
        # with a CourseOverview without more refactoring.
        course = modulestore().get_course(course_overview.id)
        tabs = []
        for priority, tab in enumerate(get_course_tab_list(self.user, course)):
            tabs.append({
                'title': tab.title,
                'slug': tab.tab_id,
                'priority': priority,
                'type': tab.type,
                'url': tab.link_func(course, reverse),
            })
        return tabs

    def get_enrollment(self, course_overview):
        """
        Return the enrollment for the logged in user.
        """
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(
            self.user,
            course_overview.id
        )
        return {'mode': mode, 'is_active': is_active}
