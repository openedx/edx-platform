"""
Tests for course access
"""


import datetime
import itertools

from unittest import mock
import pytest
import ddt
import pytz
from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from crum import set_current_request
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import _get_modulestore_branch_setting, modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_AMNESTY_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml

from lms.djangoapps.courseware.courses import (
    course_open_for_self_enrollment,
    get_cms_block_link,
    get_cms_course_link,
    get_course_about_section,
    get_course_assignments,
    get_course_chapter_ids,
    get_course_info_section,
    get_course_overview_with_access,
    get_course_with_access,
    get_courses,
    get_current_child
)
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.module_render import get_module_for_descriptor
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from openedx.core.djangolib.testing.utils import get_mock_request
from openedx.core.lib.courses import course_image_url
from openedx.core.lib.courses import get_course_by_id
from common.djangoapps.student.tests.factories import UserFactory

CMS_BASE_TEST = 'testcms'
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


@ddt.ddt
class CoursesTest(ModuleStoreTestCase):
    """Test methods related to fetching courses."""
    ENABLED_SIGNALS = ['course_published']
    GET_COURSE_WITH_ACCESS = 'get_course_with_access'
    GET_COURSE_OVERVIEW_WITH_ACCESS = 'get_course_overview_with_access'
    COURSE_ACCESS_FUNCS = {
        GET_COURSE_WITH_ACCESS: get_course_with_access,
        GET_COURSE_OVERVIEW_WITH_ACCESS: get_course_overview_with_access,
    }

    @override_settings(CMS_BASE=CMS_BASE_TEST)
    def test_get_cms_course_block_link(self):
        """
        Tests that get_cms_course_link_by_id and get_cms_block_link_by_id return the right thing
        """
        self.course = CourseFactory.create(  # lint-amnesty, pylint: disable=attribute-defined-outside-init
            org='org', number='num', display_name='name'
        )

        cms_url = f"//{CMS_BASE_TEST}/course/{str(self.course.id)}"
        assert cms_url == get_cms_course_link(self.course)
        cms_url = f"//{CMS_BASE_TEST}/course/{str(self.course.location)}"
        assert cms_url == get_cms_block_link(self.course, 'course')

    @ddt.data(GET_COURSE_WITH_ACCESS, GET_COURSE_OVERVIEW_WITH_ACCESS)
    def test_get_course_func_with_access_error(self, course_access_func_name):
        course_access_func = self.COURSE_ACCESS_FUNCS[course_access_func_name]
        user = UserFactory.create()
        course = CourseFactory.create(visible_to_staff_only=True)

        with pytest.raises(CoursewareAccessException) as error:
            course_access_func(user, 'load', course.id)
        assert str(error.value) == 'Course not found.'
        assert error.value.access_response.error_code == 'not_visible_to_user'
        assert not error.value.access_response.has_access

    @ddt.data(GET_COURSE_WITH_ACCESS, GET_COURSE_OVERVIEW_WITH_ACCESS)
    def test_old_mongo_access_error(self, course_access_func_name):
        course_access_func = self.COURSE_ACCESS_FUNCS[course_access_func_name]
        user = UserFactory.create()
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            course = CourseFactory.create()

        with pytest.raises(CourseAccessRedirect) as error:
            course_access_func(user, 'load', course.id)
        assert error.value.access_error.error_code == 'old_mongo'
        assert not error.value.access_error.has_access

    @ddt.data(
        (GET_COURSE_WITH_ACCESS, 2),
        (GET_COURSE_OVERVIEW_WITH_ACCESS, 0),
    )
    @ddt.unpack
    def test_get_course_func_with_access(self, course_access_func_name, num_mongo_calls):
        course_access_func = self.COURSE_ACCESS_FUNCS[course_access_func_name]
        user = UserFactory.create()
        course = CourseFactory.create(emit_signals=True)
        with check_mongo_calls(num_mongo_calls):
            course_access_func(user, 'load', course.id)

    def test_get_courses_by_org(self):
        """
        Verify that org filtering performs as expected, and that an empty result
        is returned if the org passed by the caller does not match the designated
        org.
        """
        primary = 'primary'
        alternate = 'alternate'

        def _fake_get_value(value, default=None):
            """Used to stub out site_configuration.helpers.get_value()."""
            if value == 'course_org_filter':
                return alternate

            return default

        user = UserFactory.create()

        # Pass `emit_signals=True` so that these courses are cached with CourseOverviews.
        primary_course = CourseFactory.create(org=primary, emit_signals=True)
        alternate_course = CourseFactory.create(org=alternate, emit_signals=True)

        assert primary_course.org != alternate_course.org

        unfiltered_courses = get_courses(user)
        for org in [primary_course.org, alternate_course.org]:
            assert any((course.org == org) for course in unfiltered_courses)

        filtered_courses = get_courses(user, org=primary)
        assert all((course.org == primary_course.org) for course in filtered_courses)

        with mock.patch(
            'openedx.core.djangoapps.site_configuration.helpers.get_value',
            autospec=True,
        ) as mock_get_value:
            mock_get_value.side_effect = _fake_get_value

            # Request filtering for an org distinct from the designated org.
            no_courses = get_courses(user, org=primary)
            assert not list(no_courses)

            # Request filtering for an org matching the designated org.
            site_courses = get_courses(user, org=alternate)
            assert all((course.org == alternate_course.org) for course in site_courses)

    def test_get_courses_with_filter(self):
        """
        Verify that filtering performs as expected.
        """
        user = UserFactory.create()
        mobile_course = CourseFactory.create(emit_signals=True)
        non_mobile_course =\
            CourseFactory.create(mobile_available=False, emit_signals=True)

        test_cases = (
            (None, {non_mobile_course.id, mobile_course.id}),
            (dict(mobile_available=True), {mobile_course.id}),
            (dict(mobile_available=False), {non_mobile_course.id}),
        )
        for filter_, expected_courses in test_cases:
            assert {course.id for course in get_courses(user, filter_=filter_)} ==\
                   expected_courses, f'testing get_courses with filter_={filter_}'

    def test_get_current_child(self):
        mock_xmodule = mock.MagicMock()
        assert get_current_child(mock_xmodule) is None

        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one', 'two', 'three']
        assert get_current_child(mock_xmodule) == 'one'

        mock_xmodule.position = 2
        assert get_current_child(mock_xmodule) == 'two'
        assert get_current_child(mock_xmodule, requested_child='first') == 'one'
        assert get_current_child(mock_xmodule, requested_child='last') == 'three'

        mock_xmodule.position = 3
        mock_xmodule.get_display_items.return_value = []
        assert get_current_child(mock_xmodule) is None


class ModuleStoreBranchSettingTest(ModuleStoreTestCase):
    """Test methods related to the modulestore branch setting."""
    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='preview.localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': ModuleStoreEnum.Branch.draft_preferred},
        MODULESTORE_BRANCH='fake_default_branch',
    )
    def test_default_modulestore_preview_mapping(self):
        assert _get_modulestore_branch_setting() == ModuleStoreEnum.Branch.draft_preferred

    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': ModuleStoreEnum.Branch.draft_preferred},
        MODULESTORE_BRANCH='fake_default_branch',
    )
    def test_default_modulestore_branch_mapping(self):
        assert _get_modulestore_branch_setting() == 'fake_default_branch'


@override_settings(CMS_BASE=CMS_BASE_TEST)
class MongoCourseImageTestCase(ModuleStoreTestCase):
    """Tests for course image URLs when using a mongo modulestore."""

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = CourseFactory.create()
        key = course.location
        assert course_image_url(course) ==\
               f'/asset-v1:{key.org}+{key.course}+{key.run}+type@asset+block@{course.course_image}'

    def test_non_ascii_image_name(self):
        # Verify that non-ascii image names are cleaned
        course = CourseFactory.create(course_image='before_\N{SNOWMAN}_after.jpg')
        key = course.location
        assert course_image_url(course) ==\
               f'/asset-v1:{key.org}+{key.course}+{key.run}+type@asset+block@before___after.jpg'

    def test_spaces_in_image_name(self):
        # Verify that image names with spaces in them are cleaned
        course = CourseFactory.create(course_image='before after.jpg')
        key = course.location
        assert course_image_url(course) ==\
               f'/asset-v1:{key.org}+{key.course}+{key.run}+type@asset+block@before_after.jpg'

    def test_static_asset_path_course_image_default(self):
        """
        Test that without course_image being set, but static_asset_path
        being set that we get the right course_image url.
        """
        course = CourseFactory.create(static_asset_path="foo")
        assert course_image_url(course) == '/static/foo/images/course_image.jpg'

    def test_static_asset_path_course_image_set(self):
        """
        Test that with course_image and static_asset_path both
        being set, that we get the right course_image url.
        """
        course = CourseFactory.create(course_image='things_stuff.jpg',
                                      static_asset_path="foo")
        assert course_image_url(course) == '/static/foo/things_stuff.jpg'


class XmlCourseImageTestCase(XModuleXmlImportTest):
    """Tests for course image URLs when using an xml modulestore."""

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = self.process_xml(xml.CourseFactory.build())
        assert course_image_url(course) == '/static/xml_test_course/images/course_image.jpg'

    def test_non_ascii_image_name(self):
        course = self.process_xml(xml.CourseFactory.build(course_image='before_\N{SNOWMAN}_after.jpg'))
        assert course_image_url(course) == '/static/xml_test_course/before_☃_after.jpg'

    def test_spaces_in_image_name(self):
        course = self.process_xml(xml.CourseFactory.build(course_image='before after.jpg'))
        assert course_image_url(course) == '/static/xml_test_course/before after.jpg'


class CoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content."""
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE

    # TODO: this test relies on the specific setup of the toy course.
    # It should be rewritten to build the course it needs and then test that.
    def setUp(self):
        """
        Set up the course and user context
        """
        super().setUp()

        store = modulestore()
        course_items = import_course_from_xml(store, self.user.id, TEST_DATA_DIR, ['toy'])
        course_key = course_items[0].id
        self.course = get_course_by_id(course_key)
        self.addCleanup(set_current_request, None)
        self.request = get_mock_request(UserFactory.create())

    def test_get_course_info_section_render(self):
        # Test render works okay
        course_info = get_course_info_section(self.request, self.request.user, self.course, 'handouts')
        assert course_info == "<a href='/c4x/edX/toy/asset/handouts_sample_handout.txt'>Sample</a>"

        # Test when render raises an exception
        with mock.patch('lms.djangoapps.courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_info = get_course_info_section(self.request, self.request.user, self.course, 'handouts')
            assert 'this module is temporarily unavailable' in course_info

    def test_get_course_about_section_render(self):

        # Test render works okay
        course_about = get_course_about_section(self.request, self.course, 'short_description')
        assert course_about == 'A course about toys.'

        # Test when render raises an exception
        with mock.patch('lms.djangoapps.courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_about = get_course_about_section(self.request, self.course, 'short_description')
            assert 'this module is temporarily unavailable' in course_about


class CourseEnrollmentOpenTests(ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def setUp(self):
        super().setUp()
        self.now = datetime.datetime.now().replace(tzinfo=pytz.UTC)

    def test_course_enrollment_open(self):
        start = self.now - datetime.timedelta(days=1)
        end = self.now + datetime.timedelta(days=1)
        course = CourseFactory(enrollment_start=start, enrollment_end=end)
        assert course_open_for_self_enrollment(course.id)

    def test_course_enrollment_closed_future(self):
        start = self.now + datetime.timedelta(days=1)
        end = self.now + datetime.timedelta(days=2)
        course = CourseFactory(enrollment_start=start, enrollment_end=end)
        assert not course_open_for_self_enrollment(course.id)

    def test_course_enrollment_closed_past(self):
        start = self.now - datetime.timedelta(days=2)
        end = self.now - datetime.timedelta(days=1)
        course = CourseFactory(enrollment_start=start, enrollment_end=end)
        assert not course_open_for_self_enrollment(course.id)

    def test_course_enrollment_dates_missing(self):
        course = CourseFactory()
        assert course_open_for_self_enrollment(course.id)

    def test_course_enrollment_dates_missing_start(self):
        end = self.now + datetime.timedelta(days=1)
        course = CourseFactory(enrollment_end=end)
        assert course_open_for_self_enrollment(course.id)

        end = self.now - datetime.timedelta(days=1)
        course = CourseFactory(enrollment_end=end)
        assert not course_open_for_self_enrollment(course.id)

    def test_course_enrollment_dates_missing_end(self):
        start = self.now - datetime.timedelta(days=1)
        course = CourseFactory(enrollment_start=start)
        assert course_open_for_self_enrollment(course.id)

        start = self.now + datetime.timedelta(days=1)
        course = CourseFactory(enrollment_start=start)
        assert not course_open_for_self_enrollment(course.id)


@ddt.ddt
class CourseInstantiationTests(ModuleStoreTestCase):
    """
    Tests around instantiating a course multiple times in the same request.
    """
    def setUp(self):
        super().setUp()

        self.factory = RequestFactory()

    @ddt.data(*itertools.product(range(5), [None, 0, 5]))
    @ddt.unpack
    def test_repeated_course_module_instantiation(self, loops, course_depth):

        with modulestore().default_store(ModuleStoreEnum.Type.split):
            course = CourseFactory.create()
            chapter = ItemFactory(parent=course, category='chapter', graded=True)
            section = ItemFactory(parent=chapter, category='sequential')
            __ = ItemFactory(parent=section, category='problem')

        fake_request = self.factory.get(
            reverse('progress', kwargs={'course_id': str(course.id)})
        )

        course = modulestore().get_course(course.id, depth=course_depth)

        for _ in range(loops):
            field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                course.id, self.user, course, depth=course_depth
            )
            course_module = get_module_for_descriptor(
                self.user,
                fake_request,
                course,
                field_data_cache,
                course.id,
                course=course
            )
            for chapter in course_module.get_children():
                for section in chapter.get_children():
                    for item in section.get_children():
                        assert item.graded


class TestGetCourseChapters(ModuleStoreTestCase):
    """
    Tests for the `get_course_chapter_ids` function.
    """

    def test_get_non_existant_course(self):
        """
        Test non-existant course returns empty list.
        """
        assert get_course_chapter_ids(None) == []
        # build a fake key
        fake_course_key = CourseKey.from_string('course-v1:FakeOrg+CN1+CR-FALLNEVER1')
        assert get_course_chapter_ids(fake_course_key) == []

    def test_get_chapters(self):
        """
        Test get_course_chapter_ids returns expected result.
        """
        course = CourseFactory()
        ItemFactory(parent=course, category='chapter')
        ItemFactory(parent=course, category='chapter')
        course_chapter_ids = get_course_chapter_ids(course.location.course_key)
        assert len(course_chapter_ids) == 2
        assert course_chapter_ids == [str(child) for child in course.children]


class TestGetCourseAssignments(CompletionWaffleTestMixin, ModuleStoreTestCase):
    """
    Tests for the `get_course_assignments` function.
    """

    def test_completion_ignores_non_scored_items(self):
        """
        Test that we treat a sequential with incomplete (but not scored) items (like a video maybe) as complete.
        """
        course = CourseFactory()
        chapter = ItemFactory(parent=course, category='chapter', graded=True, due=datetime.datetime.now(),
                              start=datetime.datetime.now() - datetime.timedelta(hours=1))
        sequential = ItemFactory(parent=chapter, category='sequential')
        problem = ItemFactory(parent=sequential, category='problem', has_score=True)
        ItemFactory(parent=sequential, category='video', has_score=False)

        self.override_waffle_switch(True)
        BlockCompletion.objects.submit_completion(self.user, problem.location, 1)

        assignments = get_course_assignments(course.location.context_key, self.user, None)
        assert len(assignments) == 1
        assert assignments[0].complete

    def test_completion_does_not_count_empty_sequentials(self):
        """
        Test that we treat a sequential with no content as incomplete.

        This can happen with unreleased assignments, for example (start date in future).
        """
        course = CourseFactory()
        chapter = ItemFactory(parent=course, category='chapter', graded=True, due=datetime.datetime.now())
        ItemFactory(parent=chapter, category='sequential')

        assignments = get_course_assignments(course.location.context_key, self.user, None)
        assert len(assignments) == 1
        assert not assignments[0].complete

    def test_completion_does_not_treat_unreleased_as_complete(self):
        """
        Test that unreleased assignments are not treated as complete.
        """
        course = CourseFactory()
        chapter = ItemFactory(parent=course, category='chapter', graded=True,
                              due=datetime.datetime.now() + datetime.timedelta(hours=2),
                              start=datetime.datetime.now() + datetime.timedelta(hours=1))
        sequential = ItemFactory(parent=chapter, category='sequential')
        problem = ItemFactory(parent=sequential, category='problem', has_score=True)
        ItemFactory(parent=sequential, category='video', has_score=False)

        self.override_waffle_switch(True)
        BlockCompletion.objects.submit_completion(self.user, problem.location, 1)

        assignments = get_course_assignments(course.location.context_key, self.user, None)
        assert len(assignments) == 1
        assert not assignments[0].complete
