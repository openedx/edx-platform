"""Tests for content.course_overviews package"""

import ddt
import itertools
import datetime

from django.test import TestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore import ModuleStoreEnum

from .models import CourseOverviewDescriptor
from courseware.tests.helpers import LoginEnrollmentTestCase

# TODO me: finish this

@ddt.ddt
class CourseOverviewDescriptorTests(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """Tests for CourseOverviewDescriptor model"""

    TODAY = datetime.datetime.now()
    YESTERDAY = TODAY - datetime.timedelta(days=1)
    TOMORROW = TODAY + datetime.timedelta(days=1)
    NEXT_MONTH = TODAY + datetime.timedelta(days=30)

    def check_course_equals_course_overview(self, course):
        """Tests that a CourseDescriptor and its corresponding CourseOverviewDescriptor behave the same.

        Specifically, given a course, test that all important attributes and methods return the same value when
        called on each of the following:
         - the CourseDescriptor itself
         - a CourseOverviewDescriptor that was newly created (the result of a cache miss)
         - a CourseOverviewDescriptor that was loaded from the MySQL database (the result of cache hit)
        """

        # Load the CourseOverviewDescriptor from the cache twice. The first load will be a cache miss (because the cache
        # is empty) so the course will be newly created with CourseOverviewDescriptor.create_from_course. The second
        # load will be a cache hit, so the course will be loaded from the cache.
        course_overview_cache_miss = CourseOverviewDescriptor.get_from_id(course.id)
        course_overview_cache_hit = CourseOverviewDescriptor.get_from_id(course.id)

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
            cache_miss_value = getattr(course_overview_cache_miss, attribute_name)
            cache_hit_value = getattr(course_overview_cache_hit, attribute_name)
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
            cache_miss_value = getattr(course_overview_cache_miss, method_name)()
            cache_hit_value = getattr(course_overview_cache_hit, method_name)()
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

    @ddt.data(*itertools.product(
        [
            {
                "static_asset_path": "/my/cool/path",
                "display_name": "Test Course",
                "start": YESTERDAY,
                "end": TOMORROW
            },
            {}
        ],
        [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split],
        [True, False]
    ))
    @ddt.unpack
    def test_course_overvewiew_behavior(self, course_kwargs, modulestore_type, is_user_enrolled):
        course = CourseFactory.create(
            course="test_course",
            org="edX",
            default_store=modulestore_type,
            **course_kwargs
        )
        self.setup_user()
        if is_user_enrolled:
            self.enroll(course, verify=True)
        self.check_course_equals_course_overview(course)

class MobileApiCourseOverviewTests(TestCase):
    """Tests to make sure the parts of the mobile API that have been changed to use this package still work right"""
    pass
