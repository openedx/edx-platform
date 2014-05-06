# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import mock

from django.test.utils import override_settings
from student.tests.factories import UserFactory
from xmodule.modulestore.django import get_default_store_name_for_current_request
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest

from courseware.courses import (
    get_course_by_id, get_cms_course_link, course_image_url,
    get_course_info_section, get_course_about_section, get_course
)
from courseware.tests.helpers import get_request_for_user
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE, TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.locations import SlashSeparatedCourseKey


CMS_BASE_TEST = 'testcms'


class CoursesTest(ModuleStoreTestCase):
    """Test methods related to fetching courses."""

    def test_get_course_by_id_invalid_chars(self):
        """
        Test that `get_course` throws a 404, rather than an exception,
        when faced with unexpected characters (such as unicode characters,
        and symbols such as = and ' ')
        """
        with self.assertRaises(Http404):
            get_course_by_id(SlashSeparatedCourseKey('MITx', 'foobar', 'business and management'))
        with self.assertRaises(Http404):
            get_course_by_id(SlashSeparatedCourseKey('MITx', 'foobar' 'statistics=introduction'))
        with self.assertRaises(Http404):
            get_course_by_id(SlashSeparatedCourseKey('MITx', 'foobar', 'NiñøJoséMaríáßç'))

    def test_get_course_invalid_chars(self):
        """
        Test that `get_course` throws a ValueError, rather than a 404,
        when faced with unexpected characters (such as unicode characters,
        and symbols such as = and ' ')
        """
        with self.assertRaises(ValueError):
            get_course(SlashSeparatedCourseKey('MITx', 'foobar', 'business and management'))
        with self.assertRaises(ValueError):
            get_course(SlashSeparatedCourseKey('MITx', 'foobar', 'statistics=introduction'))
        with self.assertRaises(ValueError):
            get_course(SlashSeparatedCourseKey('MITx', 'foobar', 'NiñøJoséMaríáßç'))

    @override_settings(
        MODULESTORE=TEST_DATA_MONGO_MODULESTORE, CMS_BASE=CMS_BASE_TEST
    )
    def test_get_cms_course_block_link(self):
        """
        Tests that get_cms_course_link_by_id and get_cms_block_link_by_id return the right thing
        """

        cms_url = u"//{}/course/org.num.name/branch/draft/block/name".format(CMS_BASE_TEST)
        self.course = CourseFactory.create(
            org='org', number='num', display_name='name'
        )

        cms_url = u"//{}/course/slashes:org+num+name".format(CMS_BASE_TEST)
        self.assertEqual(cms_url, get_cms_course_link(self.course))
        self.assertEqual(cms_url, get_cms_block_link(self.course, 'course'))

    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='preview.localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': 'draft'}
    )
    def test_default_modulestore_preview_mapping(self):
        self.assertEqual(get_default_store_name_for_current_request(), 'draft')

    @mock.patch(
        'xmodule.modulestore.django.get_current_request_hostname',
        mock.Mock(return_value='localhost')
    )
    @override_settings(
        HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': 'draft'}
    )
    def test_default_modulestore_published_mapping(self):
        self.assertEqual(get_default_store_name_for_current_request(), 'default')


@override_settings(
    MODULESTORE=TEST_DATA_MONGO_MODULESTORE, CMS_BASE=CMS_BASE_TEST
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


class XmlCourseImageTestCase(XModuleXmlImportTest):
    """Tests for course image URLs when using an xml modulestore."""

    def test_get_image_url(self):
        """Test image URL formatting."""
        course = self.process_xml(xml.CourseFactory.build())
        self.assertEquals(course_image_url(course), '/static/xml_test_course/images/course_image.jpg')

    def test_non_ascii_image_name(self):
        # XML Course images are always stored at /images/course_image.jpg
        course = self.process_xml(xml.CourseFactory.build(course_image=u'before_\N{SNOWMAN}_after.jpg'))
        self.assertEquals(course_image_url(course), '/static/xml_test_course/images/course_image.jpg')

    def test_spaces_in_image_name(self):
        # XML Course images are always stored at /images/course_image.jpg
        course = self.process_xml(xml.CourseFactory.build(course_image=u'before after.jpg'))
        self.assertEquals(course_image_url(course), '/static/xml_test_course/images/course_image.jpg')


class CoursesRenderTest(ModuleStoreTestCase):
    """Test methods related to rendering courses content."""
    toy_course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

    @override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
    def test_get_course_info_section_render(self):
        course = get_course_by_id(self.toy_course_key)
        request = get_request_for_user(UserFactory.create())

        # Test render works okay
        course_info = get_course_info_section(request, course, 'handouts')
        self.assertEqual(course_info, "<a href='/static/toy/handouts/sample_handout.txt'>Sample</a>")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_info = get_course_info_section(request, course, 'handouts')
            self.assertIn("this module is temporarily unavailable", course_info)

    @override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
    @mock.patch('courseware.courses.get_request_for_thread')
    def test_get_course_about_section_render(self, mock_get_request):
        course = get_course_by_id(self.toy_course_key)
        request = get_request_for_user(UserFactory.create())
        mock_get_request.return_value = request

        # Test render works okay
        course_about = get_course_about_section(course, 'short_description')
        self.assertEqual(course_about, "A course about toys.")

        # Test when render raises an exception
        with mock.patch('courseware.courses.get_module') as mock_module_render:
            mock_module_render.return_value = mock.MagicMock(
                render=mock.Mock(side_effect=Exception('Render failed!'))
            )
            course_about = get_course_about_section(course, 'short_description')
            self.assertIn("this module is temporarily unavailable", course_about)
