# -*- coding: utf-8 -*-
"""
Tests for course access
"""
from django.conf import settings
from django.test.utils import override_settings
import mock
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.courses import (
    get_course_by_id, get_cms_course_link, course_image_url,
    get_course_info_section, get_course_about_section, get_cms_block_link
)
from courseware.tests.helpers import get_request_for_user
from student.tests.factories import UserFactory
import xmodule.modulestore.django as store_django
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MOCK_MODULESTORE, TEST_DATA_MIXED_TOY_MODULESTORE
)
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest


CMS_BASE_TEST = 'testcms'
TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


class CoursesTest(ModuleStoreTestCase):
    """Test methods related to fetching courses."""

    @override_settings(
        MODULESTORE=TEST_DATA_MOCK_MODULESTORE, CMS_BASE=CMS_BASE_TEST
    )
    def test_get_cms_course_block_link(self):
        """
        Tests that get_cms_course_link_by_id and get_cms_block_link_by_id return the right thing
        """
        self.course = CourseFactory.create(
            org='org', number='num', display_name='name'
        )

        cms_url = u"//{}/course/org/num/name".format(CMS_BASE_TEST)
        self.assertEqual(cms_url, get_cms_course_link(self.course))
        cms_url = u"//{}/course/i4x://org/num/course/name".format(CMS_BASE_TEST)
        self.assertEqual(cms_url, get_cms_block_link(self.course, 'course'))


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
        self.assertEqual(store_django._get_modulestore_branch_setting(), ModuleStoreEnum.Branch.draft_preferred)

    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': ModuleStoreEnum.Branch.draft_preferred},
        MODULESTORE_BRANCH='fake_default_branch',
    )
    def test_default_modulestore_branch_mapping(self):
        self.assertEqual(store_django._get_modulestore_branch_setting(), 'fake_default_branch')


@override_settings(
    MODULESTORE=TEST_DATA_MOCK_MODULESTORE, CMS_BASE=CMS_BASE_TEST
)
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


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
class CoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content."""

    # TODO: this test relies on the specific setup of the toy course.
    # It should be rewritten to build the course it needs and then test that.
    def setUp(self):
        """
        Set up the course and user context
        """
        super(CoursesRenderTest, self).setUp()

        store = store_django.modulestore()
        course_items = import_from_xml(store, self.user.id, TEST_DATA_DIR, ['toy'])
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


@override_settings(MODULESTORE=TEST_DATA_MIXED_TOY_MODULESTORE)
class XmlCoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content for an XML course."""
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
