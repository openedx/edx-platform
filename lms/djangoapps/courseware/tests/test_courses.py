# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import mock
from unittest import expectedFailure

from django.http import Http404
from django.test.utils import override_settings
from xmodule.modulestore.django import get_default_store_name_for_current_request
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest

from courseware.courses import get_course_by_id, get_course, get_cms_course_link, course_image_url
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE


CMS_BASE_TEST = 'testcms'


class CoursesTest(ModuleStoreTestCase):
    """Test methods related to fetching courses."""

    def test_get_course_by_id_invalid_chars(self):
        """
        Test that `get_course_by_id` throws a 404, rather than
        an exception, when faced with unexpected characters
        (such as unicode characters, and symbols such as = and ' ')
        """
        with self.assertRaises(Http404):
            get_course_by_id('MITx/foobar/statistics=introduction')
            get_course_by_id('MITx/foobar/business and management')
            get_course_by_id('MITx/foobar/NiñøJoséMaríáßç')

    def test_get_course_invalid_chars(self):
        """
        Test that `get_course` throws a ValueError, rather than
        a 404, when faced with unexpected characters
        (such as unicode characters, and symbols such as = and ' ')
        """
        with self.assertRaises(ValueError):
            get_course('MITx/foobar/statistics=introduction')
            get_course('MITx/foobar/business and management')
            get_course('MITx/foobar/NiñøJoséMaríáßç')

    @override_settings(
        MODULESTORE=TEST_DATA_MONGO_MODULESTORE, CMS_BASE=CMS_BASE_TEST
    )
    def test_get_cms_course_link(self):
        """
        Tests that get_cms_course_link_by_id returns the right thing
        """

        self.course = CourseFactory.create(
            org='org', number='num', display_name='name'
        )

        self.assertEqual(
            u"//{}/course/org.num.name/branch/draft/block/name".format(
                CMS_BASE_TEST
            ),
            get_cms_course_link(self.course)
        )

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

    @expectedFailure
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
