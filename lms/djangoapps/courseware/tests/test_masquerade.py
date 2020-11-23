# -*- coding: utf-8 -*-
"""
Unit tests for masquerade.
"""


import json
import pickle
from datetime import datetime

import ddt
import six
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from mock import patch
from pytz import UTC
from xblock.runtime import DictKeyValueStore

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from lms.djangoapps.courseware.masquerade import (
    CourseMasquerade,
    MasqueradingKeyValueStore,
    get_masquerading_user_group
)
from lms.djangoapps.courseware.tests.factories import StaffFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase, MasqueradeMixin, masquerade_as_group_member
from lms.djangoapps.courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, set_user_preference
from openedx.features.course_experience import DISABLE_UNIFIED_COURSE_TAB_FLAG
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition


class MasqueradeTestCase(SharedModuleStoreTestCase, LoginEnrollmentTestCase, MasqueradeMixin):
    """
    Base class for masquerade tests that sets up a test course and enrolls a user in the course.
    """
    @classmethod
    def setUpClass(cls):
        super(MasqueradeTestCase, cls).setUpClass()
        cls.course = CourseFactory.create(number='masquerade-test', metadata={'start': datetime.now(UTC)})
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
                'course_id': six.text_type(self.course.id),
                'chapter': self.chapter.location.block_id,
                'section': self.sequential.location.block_id,
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
                'course_id': six.text_type(self.course.id),
            }
        )
        return self.client.get(url)

    def get_progress_page(self):
        """
        Returns the server response for progress page.
        """
        url = reverse(
            'progress',
            kwargs={
                'course_id': six.text_type(self.course.id),
            }
        )
        return self.client.get(url)

    def verify_staff_debug_present(self, staff_debug_expected):
        """
        Verifies that the staff debug control visibility is as expected (for staff only).
        """
        content = self.get_courseware_page().content.decode('utf-8')
        self.assertIn(self.sequential_display_name, content, "Subsection should be visible")
        self.assertEqual(staff_debug_expected, 'Staff Debug Info' in content)

    def get_problem(self):
        """
        Returns the JSON content for the problem in the course.
        """
        problem_url = reverse(
            'xblock_handler',
            kwargs={
                'course_id': six.text_type(self.course.id),
                'usage_id': six.text_type(self.problem.location),
                'handler': 'xmodule_handler',
                'suffix': 'problem_get'
            }
        )
        return self.client.get(problem_url)

    def verify_show_answer_present(self, show_answer_expected):
        """
        Verifies that "Show answer" is only present when expected (for staff only).
        """
        problem_html = json.loads(self.get_problem().content.decode('utf-8'))['html']
        self.assertIn(self.problem_display_name, problem_html)
        self.assertEqual(show_answer_expected, "Show answer" in problem_html)

    def ensure_masquerade_as_group_member(self, partition_id, group_id):
        """
        Installs a masquerade for the test_user and test course, to enable the
        user to masquerade as belonging to the specific partition/group combination.
        Also verifies that the call to install the masquerade was successful.

        Arguments:
            partition_id (int): the integer partition id, referring to partitions already
               configured in the course.
            group_id (int); the integer group id, within the specified partition.
        """
        self.assertEqual(200, masquerade_as_group_member(self.test_user, self.course, partition_id, group_id))


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


@ddt.ddt
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
        json_data = json.loads(self.look_at_question(self.problem_display_name).content.decode('utf-8'))
        progress = '%s/%s' % (str(json_data['current_score']), str(json_data['total_possible']))
        return progress

    def assertExpectedLanguageInPreference(self, user, expected_language_code):
        """
        This method is a custom assertion verifies that a given user has expected
        language code in the preference and in cookies.

        Arguments:
            user: User model instance
            expected_language_code: string indicating a language code
        """
        self.assertEqual(
            get_user_preference(user, LANGUAGE_KEY), expected_language_code
        )
        self.assertEqual(
            self.client.cookies[settings.LANGUAGE_COOKIE].value, expected_language_code
        )

    @override_waffle_flag(DISABLE_UNIFIED_COURSE_TAB_FLAG, active=True)
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
        self.assertContains(response, "OOGIE BLOOGIE")

        # Masquerade as the student,enable the self paced configuration, and check we can see the info page.
        SelfPacedConfiguration(enable_course_home_improvements=True).save()
        self.update_masquerade(role='student', username=self.student_user.username)
        response = self.get_course_info_page()
        self.assertContains(response, "OOGIE BLOOGIE")

    @ddt.data(
        'john',  # Non-unicode username
        u'fôô@bar',  # Unicode username with @, which is what the ENABLE_UNICODE_USERNAME feature allows
    )
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_masquerade_as_specific_student(self, username):
        """
        Test masquerading as a specific user.

        We answer the problem in our test course as the student and as staff user, and we use the
        progress as a proxy to determine who's state we currently see.
        """
        student = UserFactory.create(username=username)
        CourseEnrollment.enroll(student, self.course.id)
        self.logout()
        self.login(student.email, 'test')
        # Answer correctly as the student, and check progress.
        self.submit_answer('Correct', 'Correct')
        self.assertEqual(self.get_progress_detail(), u'2/2')

        # Log in as staff, and check the problem is unanswered.
        self.login_staff()
        self.assertEqual(self.get_progress_detail(), u'0/2')

        # Masquerade as the student, and check we can see the student state.
        self.update_masquerade(role='student', username=student.username)
        self.assertEqual(self.get_progress_detail(), u'2/2')

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
        self.logout()
        self.login(student.email, 'test')
        self.assertEqual(self.get_progress_detail(), u'2/2')

    def test_masquerading_with_language_preference(self):
        """
        Tests that masquerading as a specific user for the course does not update preference language
        for the staff.

        Login as a staff user and set user's language preference to english and visit the courseware page.
        Set masquerade to view same page as a specific student having different language preference and
        revisit the courseware page.
        """
        english_language_code = 'en'
        set_user_preference(self.test_user, preference_key=LANGUAGE_KEY, preference_value=english_language_code)
        self.login_staff()

        # Reload the page and check we have expected language preference in system and in cookies.
        self.get_courseware_page()
        self.assertExpectedLanguageInPreference(self.test_user, english_language_code)

        # Set student language preference and set masquerade to view same page the student.
        set_user_preference(self.student_user, preference_key=LANGUAGE_KEY, preference_value='es-419')
        self.update_masquerade(role='student', username=self.student_user.username)

        # Reload the page and check we have expected language preference in system and in cookies.
        self.get_courseware_page()
        self.assertExpectedLanguageInPreference(self.test_user, english_language_code)

    @override_waffle_flag(DISABLE_UNIFIED_COURSE_TAB_FLAG, active=True)
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_masquerade_as_specific_student_course_info(self):
        """
        Test masquerading as a specific user for course info page.

        We login with login_staff and check course info page content if it's working and then we
        set masquerade to view same page as a specific student and test if it's working or not.
        """
        # Log in as staff, and check we can see the info page.
        self.login_staff()
        content = self.get_course_info_page().content.decode('utf-8')
        self.assertIn("OOGIE BLOOGIE", content)

        # Masquerade as the student, and check we can see the info page.
        self.update_masquerade(role='student', username=self.student_user.username)
        content = self.get_course_info_page().content.decode('utf-8')
        self.assertIn("OOGIE BLOOGIE", content)

    def test_masquerade_as_specific_student_progress(self):
        """
        Test masquerading as a specific user for progress page.
        """
        # Give the student some correct answers, check their progress page
        self.login_student()
        self.submit_answer('Correct', 'Correct')
        student_progress = self.get_progress_page().content.decode('utf-8')
        self.assertNotIn("1 of 2 possible points", student_progress)
        self.assertIn("2 of 2 possible points", student_progress)

        # Staff answers are slightly different
        self.login_staff()
        self.submit_answer('Incorrect', 'Correct')
        staff_progress = self.get_progress_page().content.decode('utf-8')
        self.assertNotIn("2 of 2 possible points", staff_progress)
        self.assertIn("1 of 2 possible points", staff_progress)

        # Should now see the student's scores
        self.update_masquerade(role='student', username=self.student_user.username)
        masquerade_progress = self.get_progress_page().content.decode('utf-8')
        self.assertNotIn("1 of 2 possible points", masquerade_progress)
        self.assertIn("2 of 2 possible points", masquerade_progress)


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
    def test_get_masquerade_group(self):
        """
        Tests that a staff member can masquerade as being in a group in a user partition
        """
        # Verify there is no masquerading group initially
        group = get_masquerading_user_group(self.course.id, self.test_user, self.user_partition)
        self.assertIsNone(group)

        # Install a masquerading group
        self.ensure_masquerade_as_group_member(0, 1)

        # Verify that the masquerading group is returned
        group = get_masquerading_user_group(self.course.id, self.test_user, self.user_partition)
        self.assertEqual(group.id, 1)


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
