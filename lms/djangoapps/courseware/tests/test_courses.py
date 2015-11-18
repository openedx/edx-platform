# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import ddt
import itertools
import mock
from nose.plugins.attrib import attr

from django.conf import settings
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.courses import (
    get_course_by_id, get_cms_course_link, course_image_url,
    get_course_info_section, get_course_about_section, get_cms_block_link
)

from courseware.courses import get_course_with_access
from courseware.module_render import get_module_for_descriptor
from courseware.tests.helpers import get_request_for_user
from courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.courseware_access_exception import CoursewareAccessException
from student.tests.factories import UserFactory
from xmodule.modulestore.django import _get_modulestore_branch_setting, modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_TOY_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest


CMS_BASE_TEST = 'testcms'
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


@attr('shard_1')
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

    def test_get_course_with_access(self):
        user = UserFactory.create()
        course = CourseFactory.create(visible_to_staff_only=True)

        with self.assertRaises(CoursewareAccessException) as error:
            get_course_with_access(user, 'load', course.id)
        self.assertEqual(error.exception.message, "Course not found.")
        self.assertEqual(error.exception.access_response.error_code, "not_visible_to_user")
        self.assertFalse(error.exception.access_response.has_access)


@attr('shard_1')
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


@attr('shard_1')
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


@attr('shard_1')
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


@attr('shard_1')
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
        self.request = get_request_for_user(UserFactory.create())

    def test_get_course_info_section_render(self):
        # Test render works okay
        course_info = get_course_info_section(self.request, self.course, 'handouts')
        self.assertEqual(course_info, u"<a href='/c4x/edX/toy/asset/handouts_sample_handout.txt'>Sample</a>")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_info = get_course_info_section(self.request, self.course, 'handouts')
            self.assertIn("this module is temporarily unavailable", course_info)

    @mock.patch('courseware.courses.get_request_for_thread')
    def test_get_course_about_section_render(self, mock_get_request):
        mock_get_request.return_value = self.request

        # Test render works okay
        course_about = get_course_about_section(self.course, 'short_description')
        self.assertEqual(course_about, "A course about toys.")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_about = get_course_about_section(self.course, 'short_description')
            self.assertIn("this module is temporarily unavailable", course_about)


@attr('shard_1')
class XmlCoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content for an XML course."""
    MODULESTORE = TEST_DATA_MIXED_TOY_MODULESTORE

    toy_course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

    def test_get_course_info_section_render(self):
        course = get_course_by_id(self.toy_course_key)
        request = get_request_for_user(UserFactory.create())

        # Test render works okay. Note the href is different in XML courses.
        course_info = get_course_info_section(request, course, 'handouts')
        self.assertEqual(course_info, "<a href='/static/toy/handouts/sample_handout.txt'>Sample</a>")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_info = get_course_info_section(request, course, 'handouts')
            self.assertIn("this module is temporarily unavailable", course_info)


@attr('shard_1')
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
