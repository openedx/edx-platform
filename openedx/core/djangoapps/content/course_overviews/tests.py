"""Tests for content.course_overviews package"""

import ddt

from django.test import TestCase
from opaque_keys.edx.locator import CourseKey

from . import get_course_overview
from .models import CourseOverviewDescriptor
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


# TODO me: finish this

class CourseOverviewDescriptorTests(ModuleStoreTestCase):
    """Tests for CourseOverviewDescriptor model"""

    @ddt.data(

    )
    def test_course_equals_course_overview(self, course_id):
        """Tests that a CourseDescriptor and its corresponding CourseOverviewDescriptor behave the same.

        Specifically, given a course ID, test that all important attributes and methods return the same value when
        called on each of the following:
         - a CourseDescriptor
         - a CourseOverviewDescriptor that was newly created (the result of a cache miss)
         - a CourseOverviewDescriptor that was loaded from the MySQL database (the result of cache hit)
        """

        # Load up our course
        course = modulestore().get_course(course_id)

        # Delete this course from the CourseOverviewDescriptor cache, and then try to load it from the cache twice
        # (the first one will be a miss, the second a hit)
        CourseOverviewDescriptor.objects.filter(id=course_id).delete()
        course_overview_cache_miss = get_course_overview(course_id)
        course_overview_cache_hit = get_course_overview(course_id)

        # Test if all fields (other than a couple special ones) are equal between the three descriptors
        fields_to_test = [
            'id',
            'ispublic',
            'static_asset_path',
            'user_partitions',
            'visible_to_staff_only',
            'group_access',
            'enrollment_start',
            'enrollment_end',
            'start',
            'end',
            'advertised_start',
            'pre_requesite_courses',
            'end_of_course_survey_url',
            'display_name',
            'mobile_available',
            'facebook_url',
            'enrollment_domain',
            'certificates_show_before_end',
            'certificates_display_behavior',
            'course_image',
            'cert_name_short',
            'cert_name_long',
            'display_organization',
            'display_coursenumber',
            'invitation_only',
            'catalog_visiblity',
            'social_sharing_url',
            'merged_group_access',
            'location',
            'url_name',
            'display_name_with_default',
            'start_date_is_still_default',
            'number',
            'display_number_with_default',
            'org',
        ]
        for attribute_name in fields_to_test:
            course_value = getattr(course, attribute_name)
            cache_miss_value = getattr(course, attribute_name)
            cache_hit_value = getattr(course, attribute_name)
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

        # Test if return values all methods are equal between the three descriptors
        methods_to_test = [
            '_get_user_partition',
            'may_certify',
            'has_ended',
            'has_started',
            'start_datetime_text',
            'end_datetime_text',
            'clean_id',
        ]
        for method_name in methods_to_test:
            course_value = getattr(course, method_name)()
            cache_miss_value = getattr(course, method_name)()
            cache_hit_value = getattr(course, method_name)()
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

class MobileApiCourseOverviewTests(TestCase):
    """Tests to make sure the parts of the mobile API that have been changed to use this package still work right"""
    pass
