# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import itertools

import ddt
from django.conf import settings
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
import mock
from nose.plugins.attrib import attr

from courseware.courses import (
    get_cms_block_link,
    get_cms_course_link,
    get_courses,
    get_course_about_section,
    get_course_by_id,
    get_course_info_section,
    get_course_overview_with_access,
    get_course_with_access,
)
from courseware.module_render import get_module_for_descriptor
from courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from openedx.core.djangolib.testing.utils import get_mock_request
from openedx.core.lib.courses import course_image_url
from student.tests.factories import UserFactory
from xmodule.modulestore.django import _get_modulestore_branch_setting, modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory, ItemFactory, check_mongo_calls
)
from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest


CMS_BASE_TEST = 'testcms'
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


@attr(shard=1)
@ddt.ddt
class CoursesTest(ModuleStoreTestCase):
    """Test methods related to fetching courses."""

    @override_settings(CMS_BASE=CMS_BASE_TEST)
    def test_get_cms_course_block_link(self):
        """
        Tests that get_cms_course_link_by_id and get_cms_block_link_by_id return the right thing
        """
        self.course = CourseFactory.create(
            org='org', number='num', display_name='name'
        )

        cms_url = u"//{}/course/{}".format(CMS_BASE_TEST, unicode(self.course.id))
        self.assertEqual(cms_url, get_cms_course_link(self.course))
        cms_url = u"//{}/course/{}".format(CMS_BASE_TEST, unicode(self.course.location))
        self.assertEqual(cms_url, get_cms_block_link(self.course, 'course'))

    @ddt.data(get_course_with_access, get_course_overview_with_access)
    def test_get_course_func_with_access_error(self, course_access_func):
        user = UserFactory.create()
        course = CourseFactory.create(visible_to_staff_only=True)

        with self.assertRaises(CoursewareAccessException) as error:
            course_access_func(user, 'load', course.id)
        self.assertEqual(error.exception.message, "Course not found.")
        self.assertEqual(error.exception.access_response.error_code, "not_visible_to_user")
        self.assertFalse(error.exception.access_response.has_access)

    @ddt.data(
        (get_course_with_access, 1),
        (get_course_overview_with_access, 0),
    )
    @ddt.unpack
    def test_get_course_func_with_access(self, course_access_func, num_mongo_calls):
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

        self.assertNotEqual(primary_course.org, alternate_course.org)

        unfiltered_courses = get_courses(user)
        for org in [primary_course.org, alternate_course.org]:
            self.assertTrue(
                any(course.org == org for course in unfiltered_courses)
            )

        filtered_courses = get_courses(user, org=primary)
        self.assertTrue(
            all(course.org == primary_course.org for course in filtered_courses)
        )

        with mock.patch(
            'openedx.core.djangoapps.site_configuration.helpers.get_value',
            autospec=True,
        ) as mock_get_value:
            mock_get_value.side_effect = _fake_get_value

            # Request filtering for an org distinct from the designated org.
            no_courses = get_courses(user, org=primary)
            self.assertEqual(no_courses, [])

            # Request filtering for an org matching the designated org.
            site_courses = get_courses(user, org=alternate)
            self.assertTrue(
                all(course.org == alternate_course.org for course in site_courses)
            )

    def test_get_courses_with_filter(self):
        """
        Verify that filtering performs as expected.
        """
        user = UserFactory.create()
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
                    course.id
                    for course in
                    get_courses(user, filter_=filter_)
                },
                expected_courses,
                "testing get_courses with filter_={}".format(filter_),
            )


@attr(shard=1)
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
        self.assertEqual(_get_modulestore_branch_setting(), ModuleStoreEnum.Branch.draft_preferred)

    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': ModuleStoreEnum.Branch.draft_preferred},
        MODULESTORE_BRANCH='fake_default_branch',
    )
    def test_default_modulestore_branch_mapping(self):
        self.assertEqual(_get_modulestore_branch_setting(), 'fake_default_branch')


@attr(shard=1)
@override_settings(CMS_BASE=CMS_BASE_TEST)
class MongoCourseImageTestCase(ModuleStoreTestCase):
    """Tests for course image URLs when using a mongo modulestore."""

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = CourseFactory.create(org='edX', course='999')
        self.assertEquals(course_image_url(course), '/c4x/edX/999/asset/{0}'.format(course.course_image))

    def test_non_ascii_image_name(self):
        # Verify that non-ascii image names are cleaned
        course = CourseFactory.create(course_image=u'before_\N{SNOWMAN}_after.jpg')
        self.assertEquals(
            course_image_url(course),
            '/c4x/{org}/{course}/asset/before___after.jpg'.format(
                org=course.location.org,
                course=course.location.course
            )
        )

    def test_spaces_in_image_name(self):
        # Verify that image names with spaces in them are cleaned
        course = CourseFactory.create(course_image=u'before after.jpg')
        self.assertEquals(
            course_image_url(course),
            '/c4x/{org}/{course}/asset/before_after.jpg'.format(
                org=course.location.org,
                course=course.location.course
            )
        )

    def test_static_asset_path_course_image_default(self):
        """
        Test that without course_image being set, but static_asset_path
        being set that we get the right course_image url.
        """
        course = CourseFactory.create(static_asset_path="foo")
        self.assertEquals(
            course_image_url(course),
            '/static/foo/images/course_image.jpg'
        )

    def test_static_asset_path_course_image_set(self):
        """
        Test that with course_image and static_asset_path both
        being set, that we get the right course_image url.
        """
        course = CourseFactory.create(course_image=u'things_stuff.jpg',
                                      static_asset_path="foo")
        self.assertEquals(
            course_image_url(course),
            '/static/foo/things_stuff.jpg'
        )


@attr(shard=1)
class XmlCourseImageTestCase(XModuleXmlImportTest):
    """Tests for course image URLs when using an xml modulestore."""

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = self.process_xml(xml.CourseFactory.build())
        self.assertEquals(course_image_url(course), '/static/xml_test_course/images/course_image.jpg')

    def test_non_ascii_image_name(self):
        course = self.process_xml(xml.CourseFactory.build(course_image=u'before_\N{SNOWMAN}_after.jpg'))
        self.assertEquals(course_image_url(course), u'/static/xml_test_course/before_\N{SNOWMAN}_after.jpg')

    def test_spaces_in_image_name(self):
        course = self.process_xml(xml.CourseFactory.build(course_image=u'before after.jpg'))
        self.assertEquals(course_image_url(course), u'/static/xml_test_course/before after.jpg')


@attr(shard=1)
class CoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content."""

    # TODO: this test relies on the specific setup of the toy course.
    # It should be rewritten to build the course it needs and then test that.
    def setUp(self):
        """
        Set up the course and user context
        """
        super(CoursesRenderTest, self).setUp()

        store = modulestore()
        course_items = import_course_from_xml(store, self.user.id, TEST_DATA_DIR, ['toy'])
        course_key = course_items[0].id
        self.course = get_course_by_id(course_key)
        self.request = get_mock_request(UserFactory.create())

    def test_get_course_info_section_render(self):
        # Test render works okay
        course_info = get_course_info_section(self.request, self.request.user, self.course, 'handouts')
        self.assertEqual(course_info, u"<a href='/c4x/edX/toy/asset/handouts_sample_handout.txt'>Sample</a>")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_info = get_course_info_section(self.request, self.request.user, self.course, 'handouts')
            self.assertIn("this module is temporarily unavailable", course_info)

    def test_get_course_about_section_render(self):

        # Test render works okay
        course_about = get_course_about_section(self.request, self.course, 'short_description')
        self.assertEqual(course_about, "A course about toys.")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_about = get_course_about_section(self.request, self.course, 'short_description')
            self.assertIn("this module is temporarily unavailable", course_about)


@attr(shard=1)
@ddt.ddt
class CourseInstantiationTests(ModuleStoreTestCase):
    """
    Tests around instantiating a course multiple times in the same request.
    """
    def setUp(self):
        super(CourseInstantiationTests, self).setUp()

        self.factory = RequestFactory()

    @ddt.data(*itertools.product(xrange(5), [ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split], [None, 0, 5]))
    @ddt.unpack
    def test_repeated_course_module_instantiation(self, loops, default_store, course_depth):

        with modulestore().default_store(default_store):
            course = CourseFactory.create()
            chapter = ItemFactory(parent=course, category='chapter', graded=True)
            section = ItemFactory(parent=chapter, category='sequential')
            __ = ItemFactory(parent=section, category='problem')

        fake_request = self.factory.get(
            reverse('progress', kwargs={'course_id': unicode(course.id)})
        )

        course = modulestore().get_course(course.id, depth=course_depth)

        for _ in xrange(loops):
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
                        self.assertTrue(item.graded)
