"""
Tests for course_overviews app.
"""
from cStringIO import StringIO
import datetime
import ddt
import itertools
import math
import mock
from nose.plugins.attrib import attr
import pytz

from django.conf import settings
from django.test.utils import override_settings
from django.utils import timezone
from PIL import Image

from lms.djangoapps.certificates.api import get_active_web_certificate
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.courses import course_image_url
from static_replace.models import AssetBaseUrlConfig
from xmodule.assetstore.assetmgr import AssetManager
from xmodule.contentstore.django import contentstore
from xmodule.contentstore.content import StaticContent
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

from .models import CourseOverview, CourseOverviewImageSet, CourseOverviewImageConfig


@attr('shard_3')
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
            'display_name_with_default_escaped',
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
        self.assertEqual(
            {course_overview.id for course_overview in CourseOverview.get_select_courses(select_course_ids)},
            set(select_course_ids),
        )

    def test_get_all_courses(self):
        course_ids = [CourseFactory.create(emit_signals=True).id for __ in range(3)]
        self.assertEqual(
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

        self.assertEqual(
            {c.id for c in CourseOverview.get_all_courses()},
            {c.id for c in org_courses[0] + org_courses[1]},
        )

        self.assertEqual(
            {c.id for c in CourseOverview.get_all_courses(org='test_org_1')},
            {c.id for c in org_courses[1]},
        )

        # Test case-insensitivity.
        self.assertEqual(
            {c.id for c in CourseOverview.get_all_courses(org='TEST_ORG_1')},
            {c.id for c in org_courses[1]},
        )

    def test_get_all_courses_by_mobile_available(self):
        non_mobile_course = CourseFactory.create(emit_signals=True)
        mobile_course = CourseFactory.create(mobile_available=True, emit_signals=True)

        test_cases = (
            (None, {non_mobile_course.id, mobile_course.id}),
            (dict(mobile_available=True), {mobile_course.id}),
            (dict(mobile_available=False), {non_mobile_course.id}),
        )

        for filter_, expected_courses in test_cases:
            self.assertEqual(
                {
                    course_overview.id
                    for course_overview in
                    CourseOverview.get_all_courses(filter_=filter_)
                },
                expected_courses,
                "testing CourseOverview.get_all_courses with filter_={}".format(filter_),
            )


@attr('shard_3')
@ddt.ddt
class CourseOverviewImageSetTestCase(ModuleStoreTestCase):
    """
    Course thumbnail generation tests.
    """

    def setUp(self):
        """Create an active CourseOverviewImageConfig with non-default values."""
        self.set_config(True)
        super(CourseOverviewImageSetTestCase, self).setUp()

    def set_config(self, enabled):
        """
        Enable or disable thumbnail generation config.

        Config models pick the most recent by date created, descending. I delete
        entries here because that can sometimes screw up on MySQL, which only
        has second-level granularity in this timestamp.

        This uses non-default values for the dimensions.
        """
        CourseOverviewImageConfig.objects.all().delete()
        CourseOverviewImageConfig.objects.create(
            enabled=enabled,
            small_width=200,
            small_height=100,
            large_width=400,
            large_height=200
        )

    @override_settings(DEFAULT_COURSE_ABOUT_IMAGE_URL='default_course.png')
    @override_settings(STATIC_URL='static/')
    @ddt.data(
        *itertools.product(
            [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split],
            [None, '']
        )
    )
    @ddt.unpack
    def test_no_source_image(self, modulestore_type, course_image):
        """
        Tests that we behave as expected if no source image was specified.
        """
        # Because we're sending None and '', we expect to get the generic
        # fallback URL for course images.
        fallback_url = settings.STATIC_URL + settings.DEFAULT_COURSE_ABOUT_IMAGE_URL
        course_overview = self._assert_image_urls_all_default(modulestore_type, course_image, fallback_url)

        # Even though there was no source image to generate, we should still
        # have a CourseOverviewImageSet object associated with this overview.
        self.assertTrue(hasattr(course_overview, 'image_set'))

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_disabled_no_prior_data(self, modulestore_type):
        """
        Test behavior when we are disabled and no entries exist.

        1. No CourseOverviewImageSet will be created.
        2. All resolutions should return the URL of the raw source image.
        """
        # Disable model generation using config models...
        self.set_config(enabled=False)

        # Since we're disabled, we should just return the raw source image back
        # for every resolution in image_urls.
        fake_course_image = 'sample_image.png'
        course_overview = self._assert_image_urls_all_default(modulestore_type, fake_course_image)

        # Because we are disabled, no image set should have been generated.
        self.assertFalse(hasattr(course_overview, 'image_set'))

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_disabled_with_prior_data(self, modulestore_type):
        """
        Test behavior when entries have been created but we are disabled.

        This might happen because a strange bug was introduced -- e.g. we
        corrupt the images somehow when making thumbnails. Expectations:

        1. We ignore whatever was created for the thumbnails, and image_urls
           returns the same as if no thumbnails had ever been generated. So
           basically, we return the raw source image for every resolution.
        2. We keep the CourseOverviewImageSet data around for debugging
           purposes.
        """
        course_image = "my_course.jpg"
        broken_small_url = "I am small!"
        broken_large_url = "I am big!"
        with self.store.default_store(modulestore_type):
            course = CourseFactory.create(
                default_store=modulestore_type, course_image=course_image
            )
            course_overview_before = CourseOverview.get_from_id(course.id)

        # This initial seeding should create an entry for the image_set.
        self.assertTrue(hasattr(course_overview_before, 'image_set'))

        # Now just throw in some fake data to this image set, something that
        # couldn't possibly work.
        course_overview_before.image_set.small_url = broken_small_url
        course_overview_before.image_set.large_url = broken_large_url
        course_overview_before.image_set.save()

        # Now disable the thumbnail feature
        self.set_config(False)

        # Fetch a new CourseOverview
        course_overview_after = CourseOverview.get_from_id(course.id)

        # Assert that the data still exists for debugging purposes
        self.assertTrue(hasattr(course_overview_after, 'image_set'))
        image_set = course_overview_after.image_set
        self.assertEqual(image_set.small_url, broken_small_url)
        self.assertEqual(image_set.large_url, broken_large_url)

        # But because we've disabled it, asking for image_urls should give us
        # the raw source image for all resolutions, and not our broken images.
        expected_url = course_image_url(course)
        self.assertEqual(
            course_overview_after.image_urls,
            {
                'raw': expected_url,
                'small': expected_url,
                'large': expected_url
            }
        )

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_cdn(self, modulestore_type):
        """
        Test that we return CDN prefixed URLs if it is enabled.
        """
        with self.store.default_store(modulestore_type):
            course = CourseFactory.create(default_store=modulestore_type)
            overview = CourseOverview.get_from_id(course.id)

            # First the behavior when there's no CDN enabled...
            AssetBaseUrlConfig.objects.all().delete()
            if modulestore_type == ModuleStoreEnum.Type.mongo:
                expected_path_start = "/c4x/"
            elif modulestore_type == ModuleStoreEnum.Type.split:
                expected_path_start = "/asset-v1:"

            for url in overview.image_urls.values():
                self.assertTrue(url.startswith(expected_path_start))

            # Now enable the CDN...
            AssetBaseUrlConfig.objects.create(enabled=True, base_url='fakecdn.edx.org')
            expected_cdn_url = "//fakecdn.edx.org" + expected_path_start

            for url in overview.image_urls.values():
                self.assertTrue(url.startswith(expected_cdn_url))

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_cdn_with_external_image(self, modulestore_type):
        """
        Test that we return CDN prefixed URLs unless they're absolute.
        """
        with self.store.default_store(modulestore_type):
            course = CourseFactory.create(default_store=modulestore_type)
            overview = CourseOverview.get_from_id(course.id)

            # Now enable the CDN...
            AssetBaseUrlConfig.objects.create(enabled=True, base_url='fakecdn.edx.org')
            expected_cdn_url = "//fakecdn.edx.org"

            start_urls = {
                'raw': 'http://google.com/image.png',
                'small': '/static/overview.png',
                'large': ''
            }

            modified_urls = overview.apply_cdn_to_urls(start_urls)
            self.assertEqual(modified_urls['raw'], start_urls['raw'])
            self.assertNotEqual(modified_urls['small'], start_urls['small'])
            self.assertTrue(modified_urls['small'].startswith(expected_cdn_url))
            self.assertEqual(modified_urls['large'], start_urls['large'])

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_error_generating_thumbnails(self, modulestore_type):
        """
        Test a scenario where thumbnails cannot be generated.

        We need to make sure that:

        1. We don't cause any 500s to leak out. A failure to generate thumbnails
           should never cause CourseOverview generation to fail.
        2. We return the raw course image for all resolutions.
        3. We don't kill our CPU by trying over and over again.
        """
        with mock.patch('openedx.core.lib.courses.create_course_image_thumbnail') as patched_create_thumbnail:
            # Strictly speaking, this would fail anyway because there's no data
            # backing sample_image.png, but we're going to make the side-effect
            # more dramatic. ;-)
            fake_course_image = 'sample_image.png'
            patched_create_thumbnail.side_effect = Exception("Kaboom!")

            # This will generate a CourseOverview and verify that we get the
            # source image back for all resolutions.
            course_overview = self._assert_image_urls_all_default(modulestore_type, fake_course_image)

            # Make sure we were called (i.e. we tried to create the thumbnail)
            patched_create_thumbnail.assert_called()

        # Now an image set does exist, even though it only has blank values for
        # the small and large urls.
        self.assertTrue(hasattr(course_overview, 'image_set'))
        self.assertEqual(course_overview.image_set.small_url, '')
        self.assertEqual(course_overview.image_set.large_url, '')

        # The next time we create a CourseOverview, the images are explicitly
        # *not* regenerated.
        with mock.patch('openedx.core.lib.courses.create_course_image_thumbnail') as patched_create_thumbnail:
            course_overview = CourseOverview.get_from_id(course_overview.id)
            patched_create_thumbnail.assert_not_called()

    @ddt.data(
        *itertools.product(
            [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split],
            [True, False],
        )
    )
    @ddt.unpack
    def test_happy_path(self, modulestore_type, create_after_overview):
        """
        What happens when everything works like we expect it to.

        If `create_after_overview` is True, we will temporarily disable
        thumbnail creation so that the initial CourseOverview is created without
        an image_set, and the CourseOverviewImageSet is created afterwards. If
        `create_after_overview` is False, we'll create the CourseOverviewImageSet
        at the same time as the CourseOverview.
        """
        # Create a real (oversized) image...
        image = Image.new("RGB", (800, 400), "blue")
        image_buff = StringIO()
        image.save(image_buff, format="JPEG")
        image_buff.seek(0)
        image_name = "big_course_image.jpeg"

        with self.store.default_store(modulestore_type):
            course = CourseFactory.create(
                default_store=modulestore_type, course_image=image_name
            )

            # Save a real image here...
            course_image_asset_key = StaticContent.compute_location(course.id, course.course_image)
            course_image_content = StaticContent(course_image_asset_key, image_name, 'image/jpeg', image_buff)
            contentstore().save(course_image_content)

            # If create_after_overview is True, disable thumbnail generation so
            # that the CourseOverview object is created and saved without an
            # image_set at first (it will be lazily created later).
            if create_after_overview:
                self.set_config(enabled=False)

            # Now generate the CourseOverview...
            course_overview = CourseOverview.get_from_id(course.id)

            # If create_after_overview is True, no image_set exists yet. Verify
            # that, then switch config back over to True and it should lazily
            # create the image_set on the next get_from_id() call.
            if create_after_overview:
                self.assertFalse(hasattr(course_overview, 'image_set'))
                self.set_config(enabled=True)
                course_overview = CourseOverview.get_from_id(course.id)

            self.assertTrue(hasattr(course_overview, 'image_set'))
            image_urls = course_overview.image_urls
            config = CourseOverviewImageConfig.current()

            # Make sure the thumbnail names come out as expected...
            self.assertTrue(image_urls['raw'].endswith('big_course_image.jpeg'))
            self.assertTrue(image_urls['small'].endswith('big_course_image-jpeg-{}x{}.jpg'.format(*config.small)))
            self.assertTrue(image_urls['large'].endswith('big_course_image-jpeg-{}x{}.jpg'.format(*config.large)))

            # Now make sure our thumbnails are of the sizes we expect...
            for image_url, expected_size in [(image_urls['small'], config.small), (image_urls['large'], config.large)]:
                image_key = StaticContent.get_location_from_path(image_url)
                image_content = AssetManager.find(image_key)
                image = Image.open(StringIO(image_content.data))
                self.assertEqual(image.size, expected_size)

    @ddt.data(
        (800, 400),  # Larger than both, correct ratio
        (800, 600),  # Larger than both, incorrect ratio
        (300, 150),  # In between small and large, correct ratio
        (300, 180),  # In between small and large, incorrect ratio
        (100, 50),   # Smaller than both, correct ratio
        (100, 80),   # Smaller than both, incorrect ratio
        (800, 20),   # Bizarrely wide
        (20, 800),   # Bizarrely tall
    )
    def test_different_resolutions(self, src_dimensions):
        """
        Test various resolutions of images to make thumbnails of.

        Note that our test sizes are small=(200, 100) and large=(400, 200).

        1. Images should won't be blown up if it's too small, so a (100, 50)
           resolution image will remain (100, 50).
        2. However, images *will* be converted using our format and quality
           settings (JPEG, 75% -- the PIL default). This is because images with
           relatively small dimensions not compressed properly.
        3. Image thumbnail naming will maintain the naming convention of the
           target resolution, even if the image was not actually scaled to that
           size (i.e. it was already smaller). This is mostly because it's
           simpler to be consistent, but it also lets us more easily tell which
           configuration a thumbnail was created under.
        """
        # Create a source image...
        image = Image.new("RGB", src_dimensions, "blue")
        image_buff = StringIO()
        image.save(image_buff, format="PNG")
        image_buff.seek(0)
        image_name = "src_course_image.png"

        course = CourseFactory.create(course_image=image_name)

        # Save the image to the contentstore...
        course_image_asset_key = StaticContent.compute_location(course.id, course.course_image)
        course_image_content = StaticContent(course_image_asset_key, image_name, 'image/png', image_buff)
        contentstore().save(course_image_content)

        # Now generate the CourseOverview...
        config = CourseOverviewImageConfig.current()
        course_overview = CourseOverview.get_from_id(course.id)
        image_urls = course_overview.image_urls

        for image_url, target in [(image_urls['small'], config.small), (image_urls['large'], config.large)]:
            image_key = StaticContent.get_location_from_path(image_url)
            image_content = AssetManager.find(image_key)
            image = Image.open(StringIO(image_content.data))

            # Naming convention for thumbnail
            self.assertTrue(image_url.endswith('src_course_image-png-{}x{}.jpg'.format(*target)))

            # Actual thumbnail data
            src_x, src_y = src_dimensions
            target_x, target_y = target
            image_x, image_y = image.size

            # I'm basically going to assume the image library knows how to do
            # the right thing in terms of handling aspect ratio. We're just
            # going to make sure that small images aren't blown up, and that
            # we never exceed our target sizes
            self.assertLessEqual(image_x, target_x)
            self.assertLessEqual(image_y, target_y)

            if src_x < target_x and src_y < target_y:
                self.assertEqual(src_x, image_x)
                self.assertEqual(src_y, image_y)

    def test_image_creation_race_condition(self):
        """
        Test for race condition in CourseOverviewImageSet creation.

        CourseOverviewTestCase already tests for race conditions with
        CourseOverview as a whole, but we still need to test the case where a
        CourseOverview already exists and we have a race condition purely in the
        part that adds a new CourseOverviewImageSet.
        """
        # Set config to False so that we don't create the image yet
        self.set_config(False)
        course = CourseFactory.create()

        # First create our CourseOverview
        overview = CourseOverview.get_from_id(course.id)
        self.assertFalse(hasattr(overview, 'image_set'))

        # Now create an ImageSet by hand...
        CourseOverviewImageSet.objects.create(course_overview=overview)

        # Now do it the normal way -- this will cause an IntegrityError to be
        # thrown and suppressed in create_for_course()
        self.set_config(True)
        CourseOverviewImageSet.create_for_course(overview)
        self.assertTrue(hasattr(overview, 'image_set'))

        # The following is actually very important for this test because
        # set_config() does a model insert after create_for_course() has caught
        # and supressed an IntegrityError above. If create_for_course() properly
        # wraps that operation in a transaction.atomic() block, the following
        # will execute fine. If create_for_course() doesn't use an atomic block,
        # the following line will cause a TransactionManagementError because
        # Django will detect that something has already been rolled back in this
        # transaction. So we don't really care about setting the config -- it's
        # just a convenient way to cause a database write operation to happen.
        self.set_config(False)

    def _assert_image_urls_all_default(self, modulestore_type, raw_course_image_name, expected_url=None):
        """
        Helper for asserting that all image_urls are defaulting to a particular value.

        Returns the CourseOverview created. This function is useful when you
        know that the thumbnail generation process is going to fail in some way
        (e.g. unspecified source image, disabled config, runtime error) and want
        to verify that all the image URLs are a certain expected value (either
        the source image, or the fallback URL).
        """
        with self.store.default_store(modulestore_type):
            course = CourseFactory.create(
                default_store=modulestore_type, course_image=raw_course_image_name
            )
            if expected_url is None:
                expected_url = course_image_url(course)

            course_overview = CourseOverview.get_from_id(course.id)

            # All the URLs that come back should be for the expected_url
            self.assertEqual(
                course_overview.image_urls,
                {
                    'raw': expected_url,
                    'small': expected_url,
                    'large': expected_url,
                }
            )
            return course_overview
