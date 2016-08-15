"""
Tests for course_overviews app.
"""
import datetime
import ddt
import itertools
import math
import mock
import pytz

from django.utils import timezone

from lms.djangoapps.certificates.api import get_active_web_certificate
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.courses import course_image_url
from xmodule.course_metadata_utils import DEFAULT_START_DATE
from xmodule.course_module import (
    CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
    CATALOG_VISIBILITY_ABOUT,
    CATALOG_VISIBILITY_NONE,
)
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
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

    COURSE_OVERVIEW_TABS = {'courseware', 'info', 'textbooks', 'discussion', 'wiki', 'progress'}

    def check_course_overview_against_course(self, course):
        """
        Compares a CourseOverview object against its corresponding
        CourseDescriptor object.

        Specifically, given a course, test that data within the following three
        objects match each other:
         - the CourseDescriptor itself
         - a CourseOverview that was newly constructed from _create_from_course
         - a CourseOverview that was loaded from the MySQL database

        Arguments:
            course (CourseDescriptor): the course to be checked.
        """

        def get_seconds_since_epoch(date_time):
            """
            Returns the number of seconds between the Unix Epoch and the given
                datetime. If the given datetime is None, return None.

            Arguments:
                date_time (datetime): the datetime in question.
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
            'enrollment_domain',
            'invitation_only',
            'max_student_enrollments_allowed',
            'catalog_visibility',
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

        # Note: we test the time-related attributes here instead of in
        # fields_to_test, because we run into trouble while testing datetimes
        # for equality. When writing and reading dates from databases, the
        # resulting values are often off by fractions of a second. So, as a
        # workaround, we simply test if the start and end times are the same
        # number of seconds from the Unix epoch.
        time_field_accessor = lambda object, field_name: get_seconds_since_epoch(getattr(object, field_name))

        # The course about fields are accessed through the CourseDetail
        # class for the course module, and stored as attributes on the
        # CourseOverview objects.
        course_about_accessor = lambda object, field_name: CourseDetails.fetch_about_attribute(object.id, field_name)

        others_to_test = [
            ('start', time_field_accessor, time_field_accessor),
            ('end', time_field_accessor, time_field_accessor),
            ('enrollment_start', time_field_accessor, time_field_accessor),
            ('enrollment_end', time_field_accessor, time_field_accessor),
            ('announcement', time_field_accessor, time_field_accessor),

            ('short_description', course_about_accessor, getattr),
            ('effort', course_about_accessor, getattr),
            (
                'video',
                lambda c, __: CourseDetails.fetch_video_url(c.id),
                lambda c, __: c.course_video_url,
            ),
            (
                'course_image_url',
                lambda c, __: course_image_url(c),
                getattr,
            ),
            (
                'has_any_active_web_certificate',
                lambda c, field_name: get_active_web_certificate(c) is not None,
                getattr,
            ),
        ]
        for attribute_name, course_accessor, course_overview_accessor in others_to_test:
            course_value = course_accessor(course, attribute_name)
            cache_miss_value = course_overview_accessor(course_overview_cache_miss, attribute_name)
            cache_hit_value = course_overview_accessor(course_overview_cache_hit, attribute_name)
            self.assertEqual(course_value, cache_miss_value)
            self.assertEqual(cache_miss_value, cache_hit_value)

        # test tabs for both cached miss and cached hit courses
        for course_overview in [course_overview_cache_miss, course_overview_cache_hit]:
            course_overview_tabs = course_overview.tabs.all()
            course_resp_tabs = {tab.tab_id for tab in course_overview_tabs}
            self.assertEqual(self.COURSE_OVERVIEW_TABS, course_resp_tabs)

    @ddt.data(*itertools.product(
        [
            {
                "display_name": "Test Course",              # Display name provided
                "start": LAST_WEEK,                         # In the middle of the course
                "end": NEXT_WEEK,
                "announcement": LAST_MONTH,                 # Announcement date provided
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
                "catalog_visibility": CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
            },
            {
                "display_name": "",                         # Empty display name
                "start": LAST_MONTH,                        # Course already ended
                "end": LAST_WEEK,
                "advertised_start": None,                   # No advertised start
                "pre_requisite_courses": [],                # No pre-requisites
                "static_asset_path": "",                    # Empty asset path
                "certificates_show_before_end": False,
                "catalog_visibility": CATALOG_VISIBILITY_ABOUT,
            },
            {
                #                                           # Don't set display name
                "start": DEFAULT_START_DATE,                # Default start and end dates
                "end": None,
                "advertised_start": None,                   # No advertised start
                "pre_requisite_courses": [],                # No pre-requisites
                "static_asset_path": None,                  # No asset path
                "certificates_show_before_end": False,
                "catalog_visibility": CATALOG_VISIBILITY_NONE,
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
            course_kwargs (dict): kwargs to be passed to course constructor.
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """
        # Note: We specify a value for 'run' here because, for some reason,
        # .create raises an InvalidKeyError if we don't (even though my
        # other test functions don't specify a run but work fine).
        course = CourseFactory.create(default_store=modulestore_type, run="TestRun", **course_kwargs)
        self.check_course_overview_against_course(course)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_overview_cache_invalidation(self, modulestore_type):
        """
        Tests that when a course is published or deleted, the corresponding
        course_overview is removed from the cache.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """
        with self.store.default_store(modulestore_type):

            # Create a course where mobile_available is True.
            course = CourseFactory.create(mobile_available=True, default_store=modulestore_type)
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

            # Verify that when the course is deleted, the corresponding CourseOverview is deleted as well.
            with self.assertRaises(CourseOverview.DoesNotExist):
                self.store.delete_course(course.id, ModuleStoreEnum.UserID.test)
                CourseOverview.get_from_id(course.id)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_overview_caching(self, modulestore_type):
        """
        Tests that CourseOverview structures are actually getting cached.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """

        # Creating a new course will trigger a publish event and the course will be cached
        course = CourseFactory.create(default_store=modulestore_type, emit_signals=True)

        # The cache will be hit and mongo will not be queried
        with check_mongo_calls(0):
            CourseOverview.get_from_id(course.id)

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_get_non_existent_course(self, modulestore_type):
        """
        Tests that requesting a non-existent course from get_from_id raises
        CourseOverview.DoesNotExist.

        Arguments:
            modulestore_type (ModuleStoreEnum.Type): type of store to create the
                course in.
        """
        store = modulestore()._get_modulestore_by_type(modulestore_type)  # pylint: disable=protected-access
        with self.assertRaises(CourseOverview.DoesNotExist):
            CourseOverview.get_from_id(store.make_course_key('Non', 'Existent', 'Course'))

    def test_get_errored_course(self):
        """
        Test that getting an ErrorDescriptor back from the module store causes
        load_from_module_store to raise an IOError.
        """
        mock_get_course = mock.Mock(return_value=ErrorDescriptor)
        with mock.patch('xmodule.modulestore.mixed.MixedModuleStore.get_course', mock_get_course):
            # This mock makes it so when the module store tries to load course data,
            # an exception is thrown, which causes get_course to return an ErrorDescriptor,
            # which causes get_from_id to raise an IOError.
            with self.assertRaises(IOError):
                CourseOverview.load_from_module_store(self.store.make_course_key('Non', 'Existent', 'Course'))

    def test_malformed_grading_policy(self):
        """
        Test that CourseOverview handles courses with a malformed grading policy
        such that course._grading_policy['GRADE_CUTOFFS'] = {} by defaulting
        .lowest_passing_grade to None.

        Created in response to https://openedx.atlassian.net/browse/TNL-2806.
        """
        course = CourseFactory.create()
        course._grading_policy['GRADE_CUTOFFS'] = {}  # pylint: disable=protected-access
        with self.assertRaises(ValueError):
            __ = course.lowest_passing_grade
        course_overview = CourseOverview._create_from_course(course)  # pylint: disable=protected-access
        self.assertEqual(course_overview.lowest_passing_grade, None)

    @ddt.data((ModuleStoreEnum.Type.mongo, 4, 4), (ModuleStoreEnum.Type.split, 3, 4))
    @ddt.unpack
    def test_versioning(self, modulestore_type, min_mongo_calls, max_mongo_calls):
        """
        Test that CourseOverviews with old version numbers are thrown out.
        """
        with self.store.default_store(modulestore_type):
            course = CourseFactory.create()
            course_overview = CourseOverview.get_from_id(course.id)
            course_overview.version = CourseOverview.VERSION - 1
            course_overview.save()

            # Because the course overview now has an old version number, it should
            # be thrown out after being loaded from the cache, which results in
            # a call to get_course.
            with check_mongo_calls_range(max_finds=max_mongo_calls, min_finds=min_mongo_calls):
                _course_overview_2 = CourseOverview.get_from_id(course.id)

    def test_course_overview_saving_race_condition(self):
        """
        Tests that the following scenario will not cause an unhandled exception:
        - Multiple concurrent requests are made for the same non-existent CourseOverview.
        - A race condition in the django ORM's save method that checks for the presence
          of the primary key performs an Insert instead of an Update operation.
        - An IntegrityError is raised when attempting to create duplicate entries.
        - This should be handled gracefully in CourseOverview.get_from_id.

        Created in response to https://openedx.atlassian.net/browse/MA-1061.
        """
        course = CourseFactory.create()

        # mock the CourseOverview ORM to raise a DoesNotExist exception to force re-creation of the object
        with mock.patch(
            'openedx.core.djangoapps.content.course_overviews.models.CourseOverview.objects.get'
        ) as mock_getter:

            mock_getter.side_effect = CourseOverview.DoesNotExist

            # mock the CourseOverview ORM to not find the primary-key to force an Insert of the object
            with mock.patch(
                'openedx.core.djangoapps.content.course_overviews.models.CourseOverview._get_pk_val'
            ) as mock_get_pk_val:
                mock_get_pk_val.return_value = None
                # This method was not present in django 1.4. Django 1.8 calls this method if
                # _get_pk_val returns None.  This method will return empty str if there is no
                # default value present. So mock it to avoid returning the empty str as primary key
                # value. Due to empty str, model.save will do an update instead of insert which is
                # incorrect and get exception in
                # common.djangoapps.xmodule_django.models.OpaqueKeyField.get_prep_value
                with mock.patch('django.db.models.Field.get_pk_value_on_save') as mock_get_pk_value_on_save:

                    mock_get_pk_value_on_save.return_value = None

                    # The CourseOverviewTab entries can't get properly created when the CourseOverview used as a
                    # foreign key has a None 'id' - the bulk_create raises an IntegrityError. Mock out the
                    # CourseOverviewTab creation, as those record creations aren't what is being tested in this test.
                    # This mocking makes the first get_from_id() succeed with no IntegrityError - the 2nd one raises
                    # an IntegrityError for the reason listed above.
                    with mock.patch(
                        'openedx.core.djangoapps.content.course_overviews.models.CourseOverviewTab.objects.bulk_create'
                    ) as mock_bulk_create:
                        mock_bulk_create.return_value = None

                        # Verify the CourseOverview is loaded successfully both times,
                        # including after an IntegrityError exception the 2nd time.
                        for _ in range(2):
                            self.assertIsInstance(CourseOverview.get_from_id(course.id), CourseOverview)

    def test_course_overview_version_update(self):
        """
        Test that when we are running in a partially deployed state (where both
        old and new CourseOverview.VERSION values are active), that we behave
        properly. This assumes that all updates are backwards compatible, or
        at least are backwards compatible between version N and N-1.
        """
        course = CourseFactory.create()
        with mock.patch('openedx.core.djangoapps.content.course_overviews.models.CourseOverview.VERSION', new=10):
            # This will create a version 10 CourseOverview
            overview_v10 = CourseOverview.get_from_id(course.id)
            self.assertEqual(overview_v10.version, 10)

            # Now we're going to muck with the values and manually save it as v09
            overview_v10.version = 9
            overview_v10.save()

            # Now we're going to ask for it again. Because 9 < 10, we expect
            # that this entry will be deleted() and that we'll get back a new
            # entry with version = 10 again.
            updated_overview = CourseOverview.get_from_id(course.id)
            self.assertEqual(updated_overview.version, 10)

            # Now we're going to muck with this and set it a version higher in
            # the database.
            updated_overview.version = 11
            updated_overview.save()

            # Because CourseOverview is encountering a version *higher* than it
            # knows how to write, it's not going to overwrite what's there.
            unmodified_overview = CourseOverview.get_from_id(course.id)
            self.assertEqual(unmodified_overview.version, 11)

    def test_get_select_courses(self):
        course_ids = [CourseFactory.create().id for __ in range(3)]
        select_course_ids = course_ids[:len(course_ids) - 1]  # all items except the last
        self.assertSetEqual(
            {course_overview.id for course_overview in CourseOverview.get_select_courses(select_course_ids)},
            set(select_course_ids),
        )

    def test_get_all_courses(self):
        course_ids = [CourseFactory.create(emit_signals=True).id for __ in range(3)]
        self.assertSetEqual(
            {course_overview.id for course_overview in CourseOverview.get_all_courses()},
            set(course_ids),
        )

        with mock.patch(
            'openedx.core.djangoapps.content.course_overviews.models.CourseOverview.get_from_id'
        ) as mock_get_from_id:
            CourseOverview.get_all_courses()
            self.assertFalse(mock_get_from_id.called)

    def test_get_all_courses_by_org(self):
        org_courses = []  # list of lists of courses
        for index in range(2):
            org_courses.append([
                CourseFactory.create(org='test_org_' + unicode(index), emit_signals=True)
                for __ in range(3)
            ])

        self.assertSetEqual(
            {c.id for c in CourseOverview.get_all_courses(org='test_org_1')},
            {c.id for c in org_courses[1]},
        )

        self.assertSetEqual(
            {c.id for c in CourseOverview.get_all_courses()},
            {c.id for c in org_courses[0] + org_courses[1]},
        )
