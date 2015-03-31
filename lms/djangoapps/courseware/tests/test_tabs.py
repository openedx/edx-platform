"""
Test cases for tabs.
Note: Tests covering workflows in the actual tabs.py file begin after line 100
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from mock import MagicMock, Mock, patch
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.courses import get_course_by_id
from courseware.tests.helpers import get_request_for_user, LoginEnrollmentTestCase
from courseware.tests.factories import InstructorFactory, StaffFactory
from xmodule import tabs
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_TOY_MODULESTORE, TEST_DATA_MIXED_CLOSED_MODULESTORE
)

from courseware.tabs import get_course_tab_list
from courseware.views import get_static_tab_contents, static_tab
from student.tests.factories import UserFactory
from util import milestones_helpers
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class StaticTabDateTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """Test cases for Static Tab Dates."""

    MODULESTORE = TEST_DATA_MIXED_TOY_MODULESTORE

    def setUp(self):
        super(StaticTabDateTestCase, self).setUp()
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
        tab = tabs.CourseTabList.get_tab_by_slug(course.tabs, 'resources')

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


class StaticTabDateTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the static tab dates of an XML course
    """

    MODULESTORE = TEST_DATA_MIXED_CLOSED_MODULESTORE

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


class EntranceExamsTabsTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Validate tab behavior when dealing with Entrance Exams
    """
    MODULESTORE = TEST_DATA_MIXED_CLOSED_MODULESTORE

    if settings.FEATURES.get('ENTRANCE_EXAMS', False):

        def setUp(self):
            """
            Test case scaffolding
            """
            super(EntranceExamsTabsTestCase, self).setUp()

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
            self.relationship_types = milestones_helpers.get_milestone_relationship_types()
            milestones_helpers.seed_milestone_relationship_types()

        def test_get_course_tabs_list_entrance_exam_enabled(self):
            """
            Unit Test: test_get_course_tabs_list_entrance_exam_enabled
            """
            entrance_exam = ItemFactory.create(
                category="chapter",
                parent_location=self.course.location,
                data="Exam Data",
                display_name="Entrance Exam",
                is_entrance_exam=True
            )
            milestone = {
                'name': 'Test Milestone',
                'namespace': '{}.entrance_exams'.format(unicode(self.course.id)),
                'description': 'Testing Courseware Tabs'
            }
            self.user.is_staff = False
            self.course.entrance_exam_enabled = True
            self.course.entrance_exam_id = unicode(entrance_exam.location)
            milestone = milestones_helpers.add_milestone(milestone)
            milestones_helpers.add_course_milestone(
                unicode(self.course.id),
                self.relationship_types['REQUIRES'],
                milestone
            )
            milestones_helpers.add_course_content_milestone(
                unicode(self.course.id),
                unicode(entrance_exam.location),
                self.relationship_types['FULFILLS'],
                milestone
            )
            course_tab_list = get_course_tab_list(self.course, self.user)
            self.assertEqual(len(course_tab_list), 1)
            self.assertEqual(course_tab_list[0]['tab_id'], 'courseware')
            self.assertEqual(course_tab_list[0]['name'], 'Entrance Exam')

        def test_get_course_tabs_list_skipped_entrance_exam(self):
            """
            Tests tab list is not limited if user is allowed to skip entrance exam.
            """
            #create a user
            student = UserFactory()
            # login as instructor hit skip entrance exam api in instructor app
            instructor = InstructorFactory(course_key=self.course.id)
            self.client.logout()
            self.client.login(username=instructor.username, password='test')

            url = reverse('mark_student_can_skip_entrance_exam', kwargs={'course_id': unicode(self.course.id)})
            response = self.client.post(url, {
                'unique_student_identifier': student.email,
            })
            self.assertEqual(response.status_code, 200)

            # log in again as student
            self.client.logout()
            self.login(self.email, self.password)
            course_tab_list = get_course_tab_list(self.course, self.user)
            self.assertEqual(len(course_tab_list), 5)

        def test_course_tabs_list_for_staff_members(self):
            """
            Tests tab list is not limited if user is member of staff
            and has not passed entrance exam.
            """
            # Login as member of staff
            self.client.logout()
            staff_user = StaffFactory(course_key=self.course.id)
            self.client.login(username=staff_user.username, password='test')

            course_tab_list = get_course_tab_list(self.course, staff_user)
            self.assertEqual(len(course_tab_list), 5)


class TextBookTabsTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Validate tab behavior when dealing with textbooks.
    """
    MODULESTORE = TEST_DATA_MIXED_TOY_MODULESTORE

    def setUp(self):
        super(TextBookTabsTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.set_up_books(2)
        self.course.tabs = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.TextbookTabs(),
            tabs.PDFTextbookTabs(),
            tabs.HtmlTextbookTabs(),
        ]
        self.setup_user()
        self.enroll(self.course)
        self.num_textbook_tabs = sum(1 for tab in self.course.tabs if isinstance(tab, tabs.TextbookTabsBase))
        self.num_textbooks = self.num_textbook_tabs * len(self.books)

    def set_up_books(self, num_books):
        """Initializes the textbooks in the course and adds the given number of books to each textbook"""
        self.books = [MagicMock() for _ in range(num_books)]
        for book_index, book in enumerate(self.books):
            book.title = 'Book{0}'.format(book_index)
        self.course.textbooks = self.books
        self.course.pdf_textbooks = self.books
        self.course.html_textbooks = self.books

    def test_pdf_textbook_tabs(self):
        """
        Test that all textbooks tab links generating correctly.
        """
        type_to_reverse_name = {'textbook': 'book', 'pdftextbook': 'pdf_book', 'htmltextbook': 'html_book'}

        course_tab_list = get_course_tab_list(self.course, self.user)
        num_of_textbooks_found = 0
        for tab in course_tab_list:
            # Verify links of all textbook type tabs.
            if isinstance(tab, tabs.SingleTextbookTab):
                book_type, book_index = tab.tab_id.split("/", 1)
                expected_link = reverse(
                    type_to_reverse_name[book_type],
                    args=[self.course.id.to_deprecated_string(), book_index]
                )
                tab_link = tab.link_func(self.course, reverse)
                self.assertEqual(tab_link, expected_link)
                num_of_textbooks_found += 1
        self.assertEqual(num_of_textbooks_found, self.num_textbooks)
