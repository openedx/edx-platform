"""
Course API Serializers.  Representing course catalog data
"""

from babel.numbers import get_currency_symbol

from django.urls import reverse
from rest_framework import serializers

from course_modes.models import CourseMode
from edxnotes.helpers import is_feature_enabled
from lms.djangoapps.courseware.tabs import get_course_tab_list
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link

from openedx.core.lib.api.fields import AbsoluteURLField


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
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


class CourseInfoSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

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
    enrollment = serializers.DictField()
    tabs = serializers.SerializerMethodField()
    verified_mode = serializers.SerializerMethodField()
    show_calculator = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    can_load_courseware = serializers.BooleanField()
    notes = serializers.SerializerMethodField()

    # TODO: TNL-7053 Legacy: Delete these two once ready to contract
    user_has_access = serializers.BooleanField()
    user_has_staff_access = serializers.BooleanField()

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

    def get_tabs(self, course_overview):
        """
        Return course tab metadata.
        """
        tabs = []
        for priority, tab in enumerate(get_course_tab_list(course_overview.effective_user, course_overview)):
            tabs.append({
                'title': tab.title or tab.get('name', ''),
                'slug': tab.tab_id,
                'priority': priority,
                'type': tab.type,
                'url': tab.link_func(course_overview, reverse),
            })
        return tabs

    def get_verified_mode(self, course_overview):
        """
        Return verified mode information, or None.
        """
        mode = CourseMode.verified_mode_for_course(course_overview.id)
        if mode:
            return {
                'price': mode.min_price,
                'currency': mode.currency.upper(),
                'currency_symbol': get_currency_symbol(mode.currency.upper()),
                'sku': mode.sku,
                'upgrade_url': verified_upgrade_deadline_link(course_overview.effective_user, course_overview),
            }

    def get_notes(self, course_overview):
        """
        Return whether edxnotes is enabled and visible.
        """
        return {
            'enabled': is_feature_enabled(course_overview, course_overview.effective_user),
            'visible': course_overview.edxnotes_visibility,
        }
