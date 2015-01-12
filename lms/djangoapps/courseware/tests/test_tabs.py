"""
Test cases for tabs.
Note: Tests covering workflows in the actual tabs.py file begin after line 100
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test.utils import override_settings
from mock import MagicMock, Mock, patch
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.courses import get_course_by_id
from courseware.tests.helpers import get_request_for_user, LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_TOY_MODULESTORE, TEST_DATA_MIXED_CLOSED_MODULESTORE
)
from courseware.views import get_static_tab_contents, static_tab
from student.tests.factories import UserFactory
from xmodule.tabs import CourseTabList
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

if settings.FEATURES.get('MILESTONES_APP', False):
    from courseware.tabs import get_course_tab_list
    from milestones import api as milestones_api
    from milestones.models import MilestoneRelationshipType


@override_settings(MODULESTORE=TEST_DATA_MIXED_TOY_MODULESTORE)
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
            static_tab(request, course_id='edX/toy', tab_slug='new_tab')

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


@override_settings(MODULESTORE=TEST_DATA_MIXED_CLOSED_MODULESTORE)
class StaticTabDateTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the static tab dates of an XML course
    """
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


@override_settings(MODULESTORE=TEST_DATA_MIXED_CLOSED_MODULESTORE)
class EntranceExamsTabsTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Validate tab behavior when dealing with Entrance Exams
    """
    if settings.FEATURES.get('ENTRANCE_EXAMS', False):

        def setUp(self):
            """
            Test case scaffolding
            """
            self.course = CourseFactory.create()
            self.instructor_tab = ItemFactory.create(
                category="instructor", parent_location=self.course.location,
                data="Instructor Tab", display_name="Instructor"
            )
            self.extra_tab_2 = ItemFactory.create(
                category="static_tab", parent_location=self.course.location,
                data="Extra Tab", display_name="Extra Tab 2"
            )
            self.extra_tab_3 = ItemFactory.create(
                category="static_tab", parent_location=self.course.location,
                data="Extra Tab", display_name="Extra Tab 3"
            )
            self.setup_user()
            self.enroll(self.course)
            self.user.is_staff = True
            self.relationship_types = milestones_api.get_milestone_relationship_types()
            MilestoneRelationshipType.objects.create(name='requires')
            MilestoneRelationshipType.objects.create(name='fulfills')

        def test_get_course_tabs_list_entrance_exam_enabled(self):
            """
            Unit Test: test_get_course_tabs_list_entrance_exam_enabled
            """
            entrance_exam = ItemFactory.create(
                category="chapter", parent_location=self.course.location,
                data="Exam Data", display_name="Entrance Exam"
            )
            entrance_exam.is_entrance_exam = True
            milestone = {
                'name': 'Test Milestone',
                'namespace': '{}.entrance_exams'.format(unicode(self.course.id)),
                'description': 'Testing Courseware Tabs'
            }
            self.course.entrance_exam_enabled = True
            self.course.entrance_exam_id = unicode(entrance_exam.location)
            milestone = milestones_api.add_milestone(milestone)
            milestones_api.add_course_milestone(
                unicode(self.course.id),
                self.relationship_types['REQUIRES'],
                milestone
            )
            milestones_api.add_course_content_milestone(
                unicode(self.course.id),
                unicode(entrance_exam.location),
                self.relationship_types['FULFILLS'],
                milestone
            )
            course_tab_list = get_course_tab_list(self.course, self.user)
            self.assertEqual(len(course_tab_list), 2)
            self.assertEqual(course_tab_list[0]['tab_id'], 'courseware')
            self.assertEqual(course_tab_list[0]['name'], 'Entrance Exam')
            self.assertEqual(course_tab_list[1]['tab_id'], 'instructor')
