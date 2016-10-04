"""
Unit tests for masquerade.
"""
import json
import pickle
from mock import patch
from nose.plugins.attrib import attr
from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.timezone import UTC

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from courseware.masquerade import (
    CourseMasquerade,
    MasqueradingKeyValueStore,
    handle_ajax,
    setup_masquerade,
    get_masquerading_group_info
)
from courseware.tests.factories import StaffFactory
from courseware.tests.helpers import LoginEnrollmentTestCase, get_request_for_user
from courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from student.tests.factories import UserFactory
from xblock.runtime import DictKeyValueStore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.partitions.partitions import Group, UserPartition
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration


class MasqueradeTestCase(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Base class for masquerade tests that sets up a test course and enrolls a user in the course.
    """
    @classmethod
    def setUpClass(cls):
        super(MasqueradeTestCase, cls).setUpClass()
        cls.course = CourseFactory.create(number='masquerade-test', metadata={'start': datetime.now(UTC())})
        cls.info_page = ItemFactory.create(
            category="course_info", parent_location=cls.course.location,
            data="OOGIE BLOOGIE", display_name="updates"
        )
        cls.chapter = ItemFactory.create(
            parent_location=cls.course.location,
            category="chapter",
            display_name="Test Section",
        )
        cls.sequential_display_name = "Test Masquerade Subsection"
        cls.sequential = ItemFactory.create(
            parent_location=cls.chapter.location,
            category="sequential",
            display_name=cls.sequential_display_name,
        )
        cls.vertical = ItemFactory.create(
            parent_location=cls.sequential.location,
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
        cls.problem_display_name = "TestMasqueradeProblem"
        cls.problem = ItemFactory.create(
            parent_location=cls.vertical.location,
            category='problem',
            data=problem_xml,
            display_name=cls.problem_display_name
        )

    def setUp(self):
        super(MasqueradeTestCase, self).setUp()

        self.test_user = self.create_user()
        self.login(self.test_user.email, 'test')
        self.enroll(self.course, True)

    def get_courseware_page(self):
        """
        Returns the server response for the courseware page.
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

    def get_course_info_page(self):
        """
        Returns the server response for course info page.
        """
        url = reverse(
            'info',
            kwargs={
                'course_id': unicode(self.course.id),
            }
        )
        return self.client.get(url)

    def _create_mock_json_request(self, user, body, method='POST', session=None):
        """
        Returns a mock JSON request for the specified user
        """
        request = get_request_for_user(user)
        request.method = method
        request.META = {'CONTENT_TYPE': ['application/json']}
        request.body = body
        request.session = session or {}
        return request

    def verify_staff_debug_present(self, staff_debug_expected):
        """
        Verifies that the staff debug control visibility is as expected (for staff only).
        """
        content = self.get_courseware_page().content
        self.assertIn(self.sequential_display_name, content, "Subsection should be visible")
        self.assertEqual(staff_debug_expected, 'Staff Debug Info' in content)

    def get_problem(self):
        """
        Returns the JSON content for the problem in the course.
        """
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

    def verify_show_answer_present(self, show_answer_expected):
        """
        Verifies that "Show Answer" is only present when expected (for staff only).
        """
        problem_html = json.loads(self.get_problem().content)['html']
        self.assertIn(self.problem_display_name, problem_html)
        self.assertEqual(show_answer_expected, "Show Answer" in problem_html)

    def verify_real_user_profile_link(self):
        """
        Verifies that the 'Profile' link in the navigation dropdown is pointing
        to the real user.
        """
        content = self.get_courseware_page().content
        self.assertIn(
            '<a href="/u/{}" class="action dropdown-menuitem">Profile</a>'.format(self.test_user.username),
            content,
            "Profile link should point to real user",
        )


@attr(shard=1)
class NormalStudentVisibilityTest(MasqueradeTestCase):
    """
    Verify the course displays as expected for a "normal" student (to ensure test setup is correct).
    """
    def create_user(self):
        """
        Creates a normal student user.
        """
        return UserFactory()

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_staff_debug_not_visible(self):
        """
        Tests that staff debug control is not present for a student.
        """
        self.verify_staff_debug_present(False)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_show_answer_not_visible(self):
        """
        Tests that "Show Answer" is not visible for a student.
        """
        self.verify_show_answer_present(False)


class StaffMasqueradeTestCase(MasqueradeTestCase):
    """
    Base class for tests of the masquerade behavior for a staff member.
    """
    def create_user(self):
        """
        Creates a staff user.
        """
        return StaffFactory(course_key=self.course.id)

    def update_masquerade(self, role, group_id=None, user_name=None):
        """
        Toggle masquerade state.
        """
        masquerade_url = reverse(
            'masquerade_update',
            kwargs={
                'course_key_string': unicode(self.course.id),
            }
        )
        response = self.client.post(
            masquerade_url,
            json.dumps({"role": role, "group_id": group_id, "user_name": user_name}),
            "application/json"
        )
        self.assertEqual(response.status_code, 200)
        return response


@attr(shard=1)
class TestStaffMasqueradeAsStudent(StaffMasqueradeTestCase):
    """
    Check for staff being able to masquerade as student.
    """
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_staff_debug_with_masquerade(self):
        """
        Tests that staff debug control is not visible when masquerading as a student.
        """
        # Verify staff initially can see staff debug
        self.verify_staff_debug_present(True)

        # Toggle masquerade to student
        self.update_masquerade(role='student')
        self.verify_staff_debug_present(False)

        # Toggle masquerade back to staff
        self.update_masquerade(role='staff')
        self.verify_staff_debug_present(True)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_show_answer_for_staff(self):
        """
        Tests that "Show Answer" is not visible when masquerading as a student.
        """
        # Verify that staff initially can see "Show Answer".
        self.verify_show_answer_present(True)

        # Toggle masquerade to student
        self.update_masquerade(role='student')
        self.verify_show_answer_present(False)

        # Toggle masquerade back to staff
        self.update_masquerade(role='staff')
        self.verify_show_answer_present(True)


@attr(shard=1)
class TestStaffMasqueradeAsSpecificStudent(StaffMasqueradeTestCase, ProblemSubmissionTestMixin):
    """
    Check for staff being able to masquerade as a specific student.
    """
    def setUp(self):
        super(TestStaffMasqueradeAsSpecificStudent, self).setUp()
        self.student_user = self.create_user()
        self.login_student()
        self.enroll(self.course, True)

    def login_staff(self):
        """ Login as a staff user """
        self.logout()
        self.login(self.test_user.email, 'test')

    def login_student(self):
        """ Login as a student """
        self.logout()
        self.login(self.student_user.email, 'test')

    def submit_answer(self, response1, response2):
        """
        Submit an answer to the single problem in our test course.
        """
        return self.submit_question_answer(
            self.problem_display_name,
            {'2_1': response1, '2_2': response2}
        )

    def get_progress_detail(self):
        """
        Return the reported progress detail for the problem in our test course.

        The return value is a string like u'1/2'.
        """
        return json.loads(self.look_at_question(self.problem_display_name).content)['progress_detail']

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_masquerade_as_specific_user_on_self_paced(self):
        """
        Test masquerading as a specific user for course info page when self paced configuration
        "enable_course_home_improvements" flag is set

        Login as a staff user and visit course info page.
        set masquerade to view same page as a specific student and revisit the course info page.
        """
        # Log in as staff, and check we can see the info page.
        self.login_staff()
        response = self.get_course_info_page()
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertIn("OOGIE BLOOGIE", content)

        # Masquerade as the student,enable the self paced configuration, and check we can see the info page.
        SelfPacedConfiguration(enable_course_home_improvements=True).save()
        self.update_masquerade(role='student', user_name=self.student_user.username)
        response = self.get_course_info_page()
        self.assertEqual(response.status_code, 200)
        content = response.content
        self.assertIn("OOGIE BLOOGIE", content)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_masquerade_as_specific_student(self):
        """
        Test masquerading as a specific user.

        We answer the problem in our test course as the student and as staff user, and we use the
        progress as a proxy to determine who's state we currently see.
        """
        # Answer correctly as the student, and check progress.
        self.login_student()
        self.submit_answer('Correct', 'Correct')
        self.assertEqual(self.get_progress_detail(), u'2/2')

        # Log in as staff, and check the problem is unanswered.
        self.login_staff()
        self.assertEqual(self.get_progress_detail(), u'0/2')

        # Masquerade as the student, and check we can see the student state.
        self.update_masquerade(role='student', user_name=self.student_user.username)
        self.assertEqual(self.get_progress_detail(), u'2/2')

        # Verify that the user dropdown links have not changed
        self.verify_real_user_profile_link()

        # Temporarily override the student state.
        self.submit_answer('Correct', 'Incorrect')
        self.assertEqual(self.get_progress_detail(), u'1/2')

        # Reload the page and check we see the student state again.
        self.get_courseware_page()
        self.assertEqual(self.get_progress_detail(), u'2/2')

        # Become the staff user again, and check the problem is still unanswered.
        self.update_masquerade(role='staff')
        self.assertEqual(self.get_progress_detail(), u'0/2')

        # Verify the student state did not change.
        self.login_student()
        self.assertEqual(self.get_progress_detail(), u'2/2')

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_masquerade_as_specific_student_course_info(self):
        """
        Test masquerading as a specific user for course info page.

        We login with login_staff and check course info page content if it's working and then we
        set masquerade to view same page as a specific student and test if it's working or not.
        """
        # Log in as staff, and check we can see the info page.
        self.login_staff()
        content = self.get_course_info_page().content
        self.assertIn("OOGIE BLOOGIE", content)

        # Masquerade as the student, and check we can see the info page.
        self.update_masquerade(role='student', user_name=self.student_user.username)
        content = self.get_course_info_page().content
        self.assertIn("OOGIE BLOOGIE", content)


@attr(shard=1)
class TestGetMasqueradingGroupId(StaffMasqueradeTestCase):
    """
    Check for staff being able to masquerade as belonging to a group.
    """
    def setUp(self):
        super(TestGetMasqueradingGroupId, self).setUp()
        self.user_partition = UserPartition(
            0, 'Test User Partition', '',
            [Group(0, 'Group 1'), Group(1, 'Group 2')],
            scheme_id='cohort'
        )
        self.course.user_partitions.append(self.user_partition)
        modulestore().update_item(self.course, self.test_user.id)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_group_masquerade(self):
        """
        Tests that a staff member can masquerade as being in a particular group.
        """
        # Verify that there is no masquerading group initially
        group_id, user_partition_id = get_masquerading_group_info(self.test_user, self.course.id)
        self.assertIsNone(group_id)
        self.assertIsNone(user_partition_id)

        # Install a masquerading group
        request = self._create_mock_json_request(
            self.test_user,
            body='{"role": "student", "user_partition_id": 0, "group_id": 1}'
        )
        handle_ajax(request, unicode(self.course.id))
        setup_masquerade(request, self.test_user, True)

        # Verify that the masquerading group is returned
        group_id, user_partition_id = get_masquerading_group_info(self.test_user, self.course.id)
        self.assertEqual(group_id, 1)
        self.assertEqual(user_partition_id, 0)


class ReadOnlyKeyValueStore(DictKeyValueStore):
    """
    A KeyValueStore that raises an exception on attempts to modify it.

    Used to make sure MasqueradingKeyValueStore does not try to modify the underlying KeyValueStore.
    """
    def set(self, key, value):
        assert False, "ReadOnlyKeyValueStore may not be modified."

    def delete(self, key):
        assert False, "ReadOnlyKeyValueStore may not be modified."

    def set_many(self, update_dict):  # pylint: disable=unused-argument
        assert False, "ReadOnlyKeyValueStore may not be modified."


class FakeSession(dict):
    """ Mock for Django session object. """
    modified = False  # We need dict semantics with a writable 'modified' property


class MasqueradingKeyValueStoreTest(TestCase):
    """
    Unit tests for the MasqueradingKeyValueStore class.
    """
    def setUp(self):
        super(MasqueradingKeyValueStoreTest, self).setUp()
        self.ro_kvs = ReadOnlyKeyValueStore({'a': 42, 'b': None, 'c': 'OpenCraft'})
        self.session = FakeSession()
        self.kvs = MasqueradingKeyValueStore(self.ro_kvs, self.session)

    def test_all(self):
        self.assertEqual(self.kvs.get('a'), 42)
        self.assertEqual(self.kvs.get('b'), None)
        self.assertEqual(self.kvs.get('c'), 'OpenCraft')
        with self.assertRaises(KeyError):
            self.kvs.get('d')

        self.assertTrue(self.kvs.has('a'))
        self.assertTrue(self.kvs.has('b'))
        self.assertTrue(self.kvs.has('c'))
        self.assertFalse(self.kvs.has('d'))

        self.kvs.set_many({'a': 'Norwegian Blue', 'd': 'Giraffe'})
        self.kvs.set('b', 7)

        self.assertEqual(self.kvs.get('a'), 'Norwegian Blue')
        self.assertEqual(self.kvs.get('b'), 7)
        self.assertEqual(self.kvs.get('c'), 'OpenCraft')
        self.assertEqual(self.kvs.get('d'), 'Giraffe')

        for key in 'abd':
            self.assertTrue(self.kvs.has(key))
            self.kvs.delete(key)
            with self.assertRaises(KeyError):
                self.kvs.get(key)

        self.assertEqual(self.kvs.get('c'), 'OpenCraft')


class CourseMasqueradeTest(TestCase):
    """
    Unit tests for the CourseMasquerade class.
    """
    def test_unpickling_sets_all_attributes(self):
        """
        Make sure that old CourseMasquerade objects receive missing attributes when unpickled from
        the session.
        """
        cmasq = CourseMasquerade(7)
        del cmasq.user_name
        pickled_cmasq = pickle.dumps(cmasq)
        unpickled_cmasq = pickle.loads(pickled_cmasq)
        self.assertEqual(unpickled_cmasq.user_name, None)
