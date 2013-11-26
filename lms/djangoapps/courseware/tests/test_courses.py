# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import mock

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.http import Http404
from django.test.utils import override_settings
from courseware.courses import get_course_by_id, get_course, get_cms_course_link
from xmodule.modulestore.django import get_default_store_name_for_current_request
from xmodule.modulestore.tests.factories import CourseFactory
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
