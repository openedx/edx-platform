"""
Tests for course_overviews app.
"""
import datetime
import ddt
import itertools
import pytz
import math

from django.utils import timezone

from lms.djangoapps.certificates.api import get_active_web_certificate
from lms.djangoapps.courseware.courses import course_image_url
from xmodule.course_metadata_utils import DEFAULT_START_DATE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls, check_mongo_calls_range

from .models import CourseOverview


@ddt.ddt
class CourseOverviewTestCase(ModuleStoreTestCase):
    """
    Tests for CourseOverviewDescriptor model.
    """

    TODAY = timezone.now()
    LAST_MONTH = TODAY - datetime.timedelta(days=30)
    LAST_WEEK = TODAY - datetime.timedelta(days=7)
    NEXT_WEEK = TODAY + datetime.timedelta(days=7)
    NEXT_MONTH = TODAY + datetime.timedelta(days=30)

    def check_course_overview_against_course(self, course):
        """
        Compares a CourseOverview object against its corresponding
        CourseDescriptor object.

        Specifically, given a course, test that data within the following three
        objects match each other:
         - the CourseDescriptor itself
         - a CourseOverview that was newly constructed from _create_from_course
         - a CourseOverview that was loaded from the MySQL database
        """

        def get_seconds_since_epoch(date_time):
            """
            Returns the number of seconds between the Unix Epoch and the given
                datetime. If the given datetime is None, return None.
            """
            if date_time is None:
                return None
            epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
            return math.floor((date_time - epoch).total_seconds())

        # Load the CourseOverview from the cache twice. The first load will be a cache miss (because the cache
        # is empty) so the course will be newly created with CourseOverviewDescriptor.create_from_course. The second
        # load will be a cache hit, so the course will be loaded from the cache.
        course_overview_cache_miss = CourseOverview.get_from_id(course.id)
        course_overview_cache_hit = CourseOverview.get_from_id(course.id)

        # Test if value of these attributes match between the three objects
        fields_to_test = [
            'id',
            'display_name',
            'display_number_with_default',
            'display_org_with_default',
            'advertised_start',
            'facebook_url',
            'social_sharing_url',
            'certificates_display_behavior',
            'certificates_show_before_end',
            'cert_name_short',
            'cert_name_long',
            'lowest_passing_grade',
            'end_of_course_survey_url',
            'mobile_available',
            'visible_to_staff_only',
            'location',
            'number',
            'url_name',
            'display_name_with_default',
            'start_date_is_still_default',
            'pre_requisite_courses',
        ]
        for attribute_name in fields_to_test:
            course_value = getattr(course, attribute_name)
            cache_miss_value = getattr(course_overview_cache_miss, attribute_name)
            cache_hit_value = getattr(course_overview_cache_hit, attribute_name)
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

        # Test if return values for all methods are equal between the three objects
        methods_to_test = [
            ('clean_id', ()),
            ('clean_id', ('#',)),
            ('has_ended', ()),
            ('has_started', ()),
            ('start_datetime_text', ('SHORT_DATE',)),
            ('start_datetime_text', ('DATE_TIME',)),
            ('end_datetime_text', ('SHORT_DATE',)),
            ('end_datetime_text', ('DATE_TIME',)),
            ('may_certify', ()),
        ]
        for method_name, method_args in methods_to_test:
            course_value = getattr(course, method_name)(*method_args)
            cache_miss_value = getattr(course_overview_cache_miss, method_name)(*method_args)
            cache_hit_value = getattr(course_overview_cache_hit, method_name)(*method_args)
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

        # Other values to test
        # Note: we test the start and end attributes here instead of in
        # fields_to_test, because I ran into trouble while testing datetimes
        # for equality. When writing and reading dates from databases, the
        # resulting values are often off by fractions of a second. So, as a
        # workaround, we simply test if the start and end times are the same
        # number of seconds from the Unix epoch.
        others_to_test = [(
            course_image_url(course),
            course_overview_cache_miss.course_image_url,
            course_overview_cache_hit.course_image_url
        ), (
            get_active_web_certificate(course) is not None,
            course_overview_cache_miss.has_any_active_web_certificate,
            course_overview_cache_hit.has_any_active_web_certificate

        ), (
            get_seconds_since_epoch(course.start),
            get_seconds_since_epoch(course_overview_cache_miss.start),
            get_seconds_since_epoch(course_overview_cache_hit.start),
        ), (
            get_seconds_since_epoch(course.end),
            get_seconds_since_epoch(course_overview_cache_miss.end),
            get_seconds_since_epoch(course_overview_cache_hit.end),
        )]
        for (course_value, cache_miss_value, cache_hit_value) in others_to_test:
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

    @ddt.data(*itertools.product(
        [
            {
                "display_name": "Test Course",              # Display name provided
                "start": LAST_WEEK,                         # In the middle of the course
                "end": NEXT_WEEK,
                "advertised_start": "2015-01-01 11:22:33",  # Parse-able advertised_start
                "pre_requisite_courses": [                  # Has pre-requisites
                    'course-v1://edX+test1+run1',
                    'course-v1://edX+test2+run1'
                ],
                "static_asset_path": "/my/abs/path",        # Absolute path
                "certificates_show_before_end": True,
            },
            {
                "display_name": "",                         # Empty display name
                "start": NEXT_WEEK,                         # Course hasn't started yet
                "end": NEXT_MONTH,
                "advertised_start": "Very Soon!",           # Not parse-able advertised_start
                "pre_requisite_courses": [],                # No pre-requisites
                "static_asset_path": "my/relative/path",    # Relative asset path
                "certificates_show_before_end": False,
            },
            {
                "display_name": "",                         # Empty display name
                "start": LAST_MONTH,                        # Course already ended
                "end": LAST_WEEK,
                "advertised_start": None,                   # No advertised start
                "pre_requisite_courses": [],                # No pre-requisites
                "static_asset_path": "",                    # Empty asset path
                "certificates_show_before_end": False,
            },
            {
                #                                           # Don't set display name
                "start": DEFAULT_START_DATE,                # Default start and end dates
                "end": None,
                "advertised_start": None,                   # No advertised start
                "pre_requisite_courses": [],                # No pre-requisites
                "static_asset_path": None,                  # No asset path
                "certificates_show_before_end": False,
            }
        ],
        [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split]
    ))
    @ddt.unpack
    def test_course_overview_behavior(self, course_kwargs, modulestore_type):
        """
        Tests if CourseOverviews and CourseDescriptors behave the same
        by comparing pairs of them given a variety of scenarios.

        Arguments:
            course_kwargs (dict): kwargs to be passed to course constructor
            modulestore_type (ModuleStoreEnum.Type)
            is_user_enrolled (bool)
        """

        course = CourseFactory.create(
            course="TEST101",
            org="edX",
            run="Run1",
            default_store=modulestore_type,
            **course_kwargs
        )
        self.check_course_overview_against_course(course)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_overview_cache_invalidation(self, modulestore_type):
        """
        Tests that when a course is published, the corresponding
        course_overview is removed from the cache.
        """
        with self.store.default_store(modulestore_type):

            # Create a course where mobile_available is True.
            course = CourseFactory.create(
                course="TEST101",
                org="edX",
                run="Run1",
                mobile_available=True,
                default_store=modulestore_type
            )
            course_overview_1 = CourseOverview.get_from_id(course.id)
            self.assertTrue(course_overview_1.mobile_available)

            # Set mobile_available to False and update the course.
            # This fires a course_published signal, which should be caught in signals.py, which should in turn
            # delete the corresponding CourseOverview from the cache.
            course.mobile_available = False
            with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                self.store.update_item(course, ModuleStoreEnum.UserID.test)

            # Make sure that when we load the CourseOverview again, mobile_available is updated.
            course_overview_2 = CourseOverview.get_from_id(course.id)
            self.assertFalse(course_overview_2.mobile_available)

    @ddt.data((ModuleStoreEnum.Type.mongo, 1, 1), (ModuleStoreEnum.Type.split, 3, 4))
    @ddt.unpack
    def test_course_overview_caching(self, modulestore_type, min_mongo_calls, max_mongo_calls):
        """
        Tests that CourseOverview structures are actually getting cached.
        """
        course = CourseFactory.create(
            course="TEST101",
            org="edX",
            run="Run1",
            mobile_available=True,
            default_store=modulestore_type
        )

        # The first time we load a CourseOverview, it will be a cache miss, so
        # we expect the modulestore to be queried.
        with check_mongo_calls_range(max_finds=max_mongo_calls, min_finds=min_mongo_calls):
            _course_overview_1 = CourseOverview.get_from_id(course.id)

        # The second time we load a CourseOverview, it will be a cache hit, so
        # we expect no modulestore queries to be made.
        with check_mongo_calls(0):
            _course_overview_2 = CourseOverview.get_from_id(course.id)
