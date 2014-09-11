"""
Test cases for tabs.
"""
from mock import MagicMock, Mock, patch

from courseware.courses import get_course_by_id
from courseware.views import get_static_tab_contents, static_tab

from django.http import Http404
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from student.tests.factories import UserFactory
from xmodule.tabs import CourseTabList
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from courseware.tests.helpers import get_request_for_user, LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from opaque_keys.edx.locations import SlashSeparatedCourseKey


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class StaticTabDateTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """Test cases for Static Tab Dates."""

    def setUp(self):
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="static_tab", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="new_tab"
        )
        self.toy_course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

    def test_logged_in(self):
        self.setup_user()
        url = reverse('static_tab', args=[self.course.id.to_deprecated_string(), 'new_tab'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_anonymous_user(self):
        url = reverse('static_tab', args=[self.course.id.to_deprecated_string(), 'new_tab'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_invalid_course_key(self):
        request = get_request_for_user(UserFactory.create())
        with self.assertRaises(Http404):
            static_tab(request, 'edX/toy', 'new_tab')

    @override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
    def test_get_static_tab_contents(self):
        course = get_course_by_id(self.toy_course_key)
        request = get_request_for_user(UserFactory.create())
        tab = CourseTabList.get_tab_by_slug(course.tabs, 'resources')

        # Test render works okay
        tab_content = get_static_tab_contents(request, course, tab)
        self.assertIn(self.toy_course_key.to_deprecated_string(), tab_content)
        self.assertIn('static_tab', tab_content)

        # Test when render raises an exception
        with patch('courseware.views.get_module') as mock_module_render:
            mock_module_render.return_value = MagicMock(
                render=Mock(side_effect=Exception('Render failed!'))
            )
            static_tab = get_static_tab_contents(request, course, tab)
            self.assertIn("this module is temporarily unavailable", static_tab)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class StaticTabDateTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    # The following XML test course (which lives at common/test/data/2014)
    # is closed; we're testing that tabs still appear when
    # the course is already closed
    xml_course_key = SlashSeparatedCourseKey('edX', 'detached_pages', '2014')

    # this text appears in the test course's tab
    # common/test/data/2014/tabs/8e4cce2b4aaf4ba28b1220804619e41f.html
    xml_data = "static 463139"
    xml_url = "8e4cce2b4aaf4ba28b1220804619e41f"

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('static_tab', args=[self.xml_course_key.to_deprecated_string(), self.xml_url])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('static_tab', args=[self.xml_course_key.to_deprecated_string(), self.xml_url])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)
