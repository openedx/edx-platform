"""
Unit tests for masquerade

Based on (and depends on) unit tests for courseware.

Notes for running by hand:

./manage.py lms --settings test test lms/djangoapps/courseware
"""
import json

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from courseware.tests.factories import StaffFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_MOCK_MODULESTORE
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
class MasqueradeTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Base class for masquerade tests that sets up a test course.
    """
    COURSE_NUMBER = 'masquerade-test'

    def setUp(self):
        self.course = CourseFactory.create(number=self.COURSE_NUMBER)
        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="Test Section",
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name="Test Subsection",
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location,
            category="vertical",
            display_name="Test Unit",
        )
        problem_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=2,
            weight=2,
            options=['Correct', 'Incorrect'],
            correct_option='Correct'
        )
        self.problem = ItemFactory.create(
            parent_location=self.vertical.location,
            category='problem',
            data=problem_xml,
            display_name='Option Response Problem'
        )

        self.staff = StaffFactory(course_key=self.course.id)
        self.login(self.staff.email, 'test')
        self.enroll(self.course)


class TestStaffMasqueradeAsStudent(MasqueradeTestCase):
    """
    Check for staff being able to masquerade as student.
    """
    def get_courseware_page(self):
        """
        Returns the HTML rendering for the courseware page.
        """
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(self.course.id),
                'chapter': self.chapter.location.name,
                'section': self.sequential.location.name,
            }
        )
        return self.client.get(url)

    def test_staff_debug_for_staff(self):
        courseware_response = self.get_courseware_page()
        self.assertTrue('Staff Debug Info' in courseware_response.content)

    def update_masquerade(self, role, group_id=None):
        """
        Toggle masquerade state.
        """
        masquerade_url = reverse(
            'masquerade_update',
            kwargs={
                'course_key_string': unicode(self.course.id),
            }
        )
        return self.client.post(masquerade_url, {"role": role, "group_id": group_id})

    def test_no_staff_debug_for_student(self):
        masquerade_response = self.update_masquerade(role='student')
        self.assertEqual(masquerade_response.status_code, 204)

        courseware_response = self.get_courseware_page()

        self.assertFalse('Staff Debug Info' in courseware_response.content)

    def get_problem(self):
        problem_url = reverse(
            'xblock_handler',
            kwargs={
                'course_id': unicode(self.course.id),
                'usage_id': unicode(self.problem.location),
                'handler': 'xmodule_handler',
                'suffix': 'problem_get'
            }
        )
        return self.client.get(problem_url)

    def test_show_answer_for_staff(self):
        problem_response = self.get_problem()
        html = json.loads(problem_response.content)['html']
        expected_html = (
            '<button class="show"><span class="show-label">Show Answer</span> '
            '<span class="sr">Reveal Answer</span></button>'
        )
        self.assertTrue(expected_html in html)

    def test_no_show_answer_for_student(self):
        masquerade_response = self.update_masquerade(role='student')
        self.assertEqual(masquerade_response.status_code, 204)

        problem_response = self.get_problem()
        html = json.loads(problem_response.content)['html']
        expected_html = (
            '<button class="show"><span class="show-label" aria-hidden="true">Show Answer</span> '
            '<span class="sr">Reveal answer above</span></button>'
        )
        self.assertFalse(expected_html in html)
