"""
Tests for content.course_overviews package
"""

import datetime
from dateutil.tz import tzutc
import ddt
import itertools

from django.utils import timezone

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore import ModuleStoreEnum

from courseware.tests.helpers import LoginEnrollmentTestCase
from .models import CourseOverviewDescriptor

@ddt.ddt
class CourseOverviewDescriptorTests(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for CourseOverviewDescriptor model.
    """

    TODAY = timezone.now()
    YESTERDAY = TODAY - datetime.timedelta(days=1)
    TOMORROW = TODAY + datetime.timedelta(days=1)
    NEXT_MONTH = TODAY + datetime.timedelta(days=30)

    def check_course_equals_course_overview(self, course):
        """Checks if a CourseDescriptor behaves the same as its CourseOverviewDescriptor.

        Specifically, given a course, test that all important attributes and
        methods return the same value when called on each of the following:
         - the CourseDescriptor itself
         - a CourseOverviewDescriptor that was newly created from it
         - a CourseOverviewDescriptor that was loaded from the MySQL database
        """

        # Load the CourseOverviewDescriptor from the cache twice. The first load will be a cache miss (because the cache
        # is empty) so the course will be newly created with CourseOverviewDescriptor.create_from_course. The second
        # load will be a cache hit, so the course will be loaded from the cache.
        course_overview_cache_miss = CourseOverviewDescriptor.get_from_id(course.id)
        course_overview_cache_hit = CourseOverviewDescriptor.get_from_id(course.id)

        # Test if the majority of the fields are equal between the three descriptors
        # Fields we don't test:
        #   - modulestore_type and _location, because they are specific to CourseOverviewDescriptor.
        #   - start, end, enrollment_start and enrollment_end because testing equality between
        #     datetimes is not reliable. Often, two datetimes that *should* be considered equal
        #     will compare as "not equal" due to a subtle nuance in how they are stored. Anyway,
        #     we check start_datetime_text() and end_datetime_text() so we don't have to worry
        #     about not testing the datetime objects.
        fields_to_test = [
            'id',
            'ispublic',
            'static_asset_path',
            'user_partitions',
            'visible_to_staff_only',
            'group_access',
            'advertised_start',
            'pre_requisite_courses',
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
            'catalog_visibility',
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
        """Tests if CourseOverviews and CourseOverviewDescriptors behave the same
        by comparing pairs of them given a variety of scenarios.

        Args:
            course_kwargs (dict): kwargs to be passed to course constructor
            modulestore_type (ModuleStoreEnum.Type)
            is_user_enrolled (bool)
        """
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
