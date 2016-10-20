# -*- coding: utf-8 -*-
"""
Unit tests for instructor.enrollment methods.
"""

import json
import mock
from mock import patch
from abc import ABCMeta
from courseware.models import StudentModule
from courseware.tests.helpers import get_request_for_user
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import override as override_language
from nose.plugins.attrib import attr
from ccx_keys.locator import CCXLocator
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from grades.new.subsection_grade import SubsectionGradeFactory
from grades.tests.utils import answer_problem
from lms.djangoapps.ccx.tests.factories import CcxFactory
from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory
)
from lms.djangoapps.instructor.enrollment import (
    EmailEnrollmentState,
    enroll_email,
    get_email_params,
    reset_student_attempts,
    send_beta_role_email,
    unenroll_email,
    render_message_to_string,
)
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from submissions import api as sub_api
from student.models import anonymous_id_for_user
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE


@attr(shard=1)
class TestSettableEnrollmentState(CacheIsolationTestCase):
    """ Test the basis class for enrollment tests. """
    def setUp(self):
        super(TestSettableEnrollmentState, self).setUp()
        self.course_key = SlashSeparatedCourseKey('Robot', 'fAKE', 'C-%-se-%-ID')

    def test_mes_create(self):
        """
        Test SettableEnrollmentState creation of user.
        """
        mes = SettableEnrollmentState(
            user=True,
            enrollment=True,
            allowed=False,
            auto_enroll=False
        )
        # enrollment objects
        eobjs = mes.create_user(self.course_key)
        ees = EmailEnrollmentState(self.course_key, eobjs.email)
        self.assertEqual(mes, ees)


class TestEnrollmentChangeBase(CacheIsolationTestCase):
    """
    Test instructor enrollment administration against database effects.

    Test methods in derived classes follow a strict format.
    `action` is a function which is run
    the test will pass if `action` mutates state from `before_ideal` to `after_ideal`
    """

    __metaclass__ = ABCMeta

    def setUp(self):
        super(TestEnrollmentChangeBase, self).setUp()
        self.course_key = SlashSeparatedCourseKey('Robot', 'fAKE', 'C-%-se-%-ID')

    def _run_state_change_test(self, before_ideal, after_ideal, action):
        """
        Runs a state change test.

        `before_ideal` and `after_ideal` are SettableEnrollmentState's
        `action` is a function which will be run in the middle.
            `action` should transition the world from before_ideal to after_ideal
            `action` will be supplied the following arguments (None-able arguments)
                `email` is an email string
        """
        # initialize & check before
        print "checking initialization..."
        eobjs = before_ideal.create_user(self.course_key)
        before = EmailEnrollmentState(self.course_key, eobjs.email)
        self.assertEqual(before, before_ideal)

        # do action
        print "running action..."
        action(eobjs.email)

        # check after
        print "checking effects..."
        after = EmailEnrollmentState(self.course_key, eobjs.email)
        self.assertEqual(after, after_ideal)


@attr(shard=1)
class TestInstructorEnrollDB(TestEnrollmentChangeBase):
    """ Test instructor.enrollment.enroll_email """
    def test_enroll(self):
        before_ideal = SettableEnrollmentState(
            user=True,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        after_ideal = SettableEnrollmentState(
            user=True,
            enrollment=True,
            allowed=False,
            auto_enroll=False
        )

        action = lambda email: enroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_enroll_again(self):
        before_ideal = SettableEnrollmentState(
            user=True,
            enrollment=True,
            allowed=False,
            auto_enroll=False,
        )

        after_ideal = SettableEnrollmentState(
            user=True,
            enrollment=True,
            allowed=False,
            auto_enroll=False,
        )

        action = lambda email: enroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_enroll_nouser(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=False,
            auto_enroll=False,
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=False,
        )

        action = lambda email: enroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_enroll_nouser_again(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=False
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=False,
        )

        action = lambda email: enroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_enroll_nouser_autoenroll(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=False,
            auto_enroll=False,
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=True,
        )

        action = lambda email: enroll_email(self.course_key, email, auto_enroll=True)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_enroll_nouser_change_autoenroll(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=True,
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=False,
        )

        action = lambda email: enroll_email(self.course_key, email, auto_enroll=False)

        return self._run_state_change_test(before_ideal, after_ideal, action)


@attr(shard=1)
class TestInstructorUnenrollDB(TestEnrollmentChangeBase):
    """ Test instructor.enrollment.unenroll_email """
    def test_unenroll(self):
        before_ideal = SettableEnrollmentState(
            user=True,
            enrollment=True,
            allowed=False,
            auto_enroll=False
        )

        after_ideal = SettableEnrollmentState(
            user=True,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        action = lambda email: unenroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_unenroll_notenrolled(self):
        before_ideal = SettableEnrollmentState(
            user=True,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        after_ideal = SettableEnrollmentState(
            user=True,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        action = lambda email: unenroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_unenroll_disallow(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=True,
            auto_enroll=True
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        action = lambda email: unenroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)

    def test_unenroll_norecord(self):
        before_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        after_ideal = SettableEnrollmentState(
            user=False,
            enrollment=False,
            allowed=False,
            auto_enroll=False
        )

        action = lambda email: unenroll_email(self.course_key, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)


@attr(shard=1)
class TestInstructorEnrollmentStudentModule(SharedModuleStoreTestCase):
    """ Test student module manipulations. """
    @classmethod
    def setUpClass(cls):
        super(TestInstructorEnrollmentStudentModule, cls).setUpClass()
        cls.course = CourseFactory(
            name='fake',
            org='course',
            run='id',
        )
        # pylint: disable=no-member
        cls.course_key = cls.course.location.course_key
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            cls.parent = ItemFactory(
                category="library_content",
                parent=cls.course,
                publish_item=True,
            )
            cls.child = ItemFactory(
                category="html",
                parent=cls.parent,
                publish_item=True,
            )
            cls.unrelated = ItemFactory(
                category="html",
                parent=cls.course,
                publish_item=True,
            )

    def setUp(self):
        super(TestInstructorEnrollmentStudentModule, self).setUp()

        self.user = UserFactory()

        parent_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        child_state = json.dumps({'attempts': 10, 'whatever': 'things'})
        unrelated_state = json.dumps({'attempts': 12, 'brains': 'zombie'})
        StudentModule.objects.create(
            student=self.user,
            course_id=self.course_key,
            module_state_key=self.parent.location,
            state=parent_state,
        )
        StudentModule.objects.create(
            student=self.user,
            course_id=self.course_key,
            module_state_key=self.child.location,
            state=child_state,
        )
        StudentModule.objects.create(
            student=self.user,
            course_id=self.course_key,
            module_state_key=self.unrelated.location,
            state=unrelated_state,
        )

    def test_reset_student_attempts(self):
        msk = self.course_key.make_usage_key('dummy', 'module')
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        StudentModule.objects.create(
            student=self.user,
            course_id=self.course_key,
            module_state_key=msk,
            state=original_state
        )
        # lambda to reload the module state from the database
        module = lambda: StudentModule.objects.get(student=self.user, course_id=self.course_key, module_state_key=msk)
        self.assertEqual(json.loads(module().state)['attempts'], 32)
        reset_student_attempts(self.course_key, self.user, msk, requesting_user=self.user)
        self.assertEqual(json.loads(module().state)['attempts'], 0)

    @mock.patch('lms.djangoapps.grades.signals.handlers.SCORE_CHANGED.send')
    def test_delete_student_attempts(self, _mock_signal):
        msk = self.course_key.make_usage_key('dummy', 'module')
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        StudentModule.objects.create(
            student=self.user,
            course_id=self.course_key,
            module_state_key=msk,
            state=original_state
        )
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.user,
                course_id=self.course_key,
                module_state_key=msk
            ).count(), 1)
        reset_student_attempts(self.course_key, self.user, msk, requesting_user=self.user, delete_module=True)
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.user,
                course_id=self.course_key,
                module_state_key=msk
            ).count(), 0)

    # Disable the score change signal to prevent other components from being
    # pulled into tests.
    @mock.patch('lms.djangoapps.grades.signals.handlers.SCORE_CHANGED.send')
    def test_delete_submission_scores(self, _mock_signal):
        user = UserFactory()
        problem_location = self.course_key.make_usage_key('dummy', 'module')

        # Create a student module for the user
        StudentModule.objects.create(
            student=user,
            course_id=self.course_key,
            module_state_key=problem_location,
            state=json.dumps({})
        )

        # Create a submission and score for the student using the submissions API
        student_item = {
            'student_id': anonymous_id_for_user(user, self.course_key),
            'course_id': self.course_key.to_deprecated_string(),
            'item_id': problem_location.to_deprecated_string(),
            'item_type': 'openassessment'
        }
        submission = sub_api.create_submission(student_item, 'test answer')
        sub_api.set_score(submission['uuid'], 1, 2)

        # Delete student state using the instructor dash
        reset_student_attempts(
            self.course_key, user, problem_location,
            requesting_user=user,
            delete_module=True,
        )

        # Verify that the student's scores have been reset in the submissions API
        score = sub_api.get_score(student_item)
        self.assertIs(score, None)

    def get_state(self, location):
        """Reload and grab the module state from the database"""
        return StudentModule.objects.get(
            student=self.user, course_id=self.course_key, module_state_key=location
        ).state

    def test_reset_student_attempts_children(self):
        parent_state = json.loads(self.get_state(self.parent.location))
        self.assertEqual(parent_state['attempts'], 32)
        self.assertEqual(parent_state['otherstuff'], 'alsorobots')

        child_state = json.loads(self.get_state(self.child.location))
        self.assertEqual(child_state['attempts'], 10)
        self.assertEqual(child_state['whatever'], 'things')

        unrelated_state = json.loads(self.get_state(self.unrelated.location))
        self.assertEqual(unrelated_state['attempts'], 12)
        self.assertEqual(unrelated_state['brains'], 'zombie')

        reset_student_attempts(self.course_key, self.user, self.parent.location, requesting_user=self.user)

        parent_state = json.loads(self.get_state(self.parent.location))
        self.assertEqual(json.loads(self.get_state(self.parent.location))['attempts'], 0)
        self.assertEqual(parent_state['otherstuff'], 'alsorobots')

        child_state = json.loads(self.get_state(self.child.location))
        self.assertEqual(child_state['attempts'], 0)
        self.assertEqual(child_state['whatever'], 'things')

        unrelated_state = json.loads(self.get_state(self.unrelated.location))
        self.assertEqual(unrelated_state['attempts'], 12)
        self.assertEqual(unrelated_state['brains'], 'zombie')

    def test_delete_submission_scores_attempts_children(self):
        parent_state = json.loads(self.get_state(self.parent.location))
        self.assertEqual(parent_state['attempts'], 32)
        self.assertEqual(parent_state['otherstuff'], 'alsorobots')

        child_state = json.loads(self.get_state(self.child.location))
        self.assertEqual(child_state['attempts'], 10)
        self.assertEqual(child_state['whatever'], 'things')

        unrelated_state = json.loads(self.get_state(self.unrelated.location))
        self.assertEqual(unrelated_state['attempts'], 12)
        self.assertEqual(unrelated_state['brains'], 'zombie')

        reset_student_attempts(
            self.course_key,
            self.user,
            self.parent.location,
            requesting_user=self.user,
            delete_module=True,
        )

        self.assertRaises(StudentModule.DoesNotExist, self.get_state, self.parent.location)
        self.assertRaises(StudentModule.DoesNotExist, self.get_state, self.child.location)

        unrelated_state = json.loads(self.get_state(self.unrelated.location))
        self.assertEqual(unrelated_state['attempts'], 12)
        self.assertEqual(unrelated_state['brains'], 'zombie')


class TestStudentModuleGrading(SharedModuleStoreTestCase):
    """
    Tests the effects of student module manipulations
    on student grades.
    """
    @classmethod
    def setUpClass(cls):
        super(TestStudentModuleGrading, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(
            parent=cls.course,
            category="chapter",
            display_name="Test Chapter"
        )
        cls.sequence = ItemFactory.create(
            parent=cls.chapter,
            category='sequential',
            display_name="Test Sequential 1",
            graded=True
        )
        cls.vertical = ItemFactory.create(
            parent=cls.sequence,
            category='vertical',
            display_name='Test Vertical 1'
        )
        problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
            question_text='The correct answer is Choice 3',
            choices=[False, False, True, False],
            choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
        )
        cls.problem = ItemFactory.create(
            parent=cls.vertical,
            category="problem",
            display_name="Test Problem",
            data=problem_xml
        )
        cls.request = get_request_for_user(UserFactory())
        cls.user = cls.request.user

    def _get_subsection_grade_and_verify(self, all_earned, all_possible, graded_earned, graded_possible):
        """
        Retrieves the subsection grade and verifies that
        its scores match those expected.
        """
        subsection_grade_factory = SubsectionGradeFactory(
            self.user,
            self.course,
            get_course_blocks(self.user, self.course.location)
        )
        grade = subsection_grade_factory.create(self.sequence)
        self.assertEqual(grade.all_total.earned, all_earned)
        self.assertEqual(grade.graded_total.earned, graded_earned)
        self.assertEqual(grade.all_total.possible, all_possible)
        self.assertEqual(grade.graded_total.possible, graded_possible)

    @patch('crum.get_current_request')
    def test_delete_student_state(self, _crum_mock):
        problem_location = self.problem.location
        self._get_subsection_grade_and_verify(0, 1, 0, 1)
        answer_problem(course=self.course, request=self.request, problem=self.problem, score=1, max_value=1)
        self._get_subsection_grade_and_verify(1, 1, 1, 1)

        # Delete student state using the instructor dash
        reset_student_attempts(
            self.course.id,
            self.user,
            problem_location,
            requesting_user=self.user,
            delete_module=True,
        )
        # Verify that the student's grades are reset
        self._get_subsection_grade_and_verify(0, 1, 0, 1)


class EnrollmentObjects(object):
    """
    Container for enrollment objects.

    `email` - student email
    `user` - student User object
    `cenr` - CourseEnrollment object
    `cea` - CourseEnrollmentAllowed object

    Any of the objects except email can be None.
    """
    def __init__(self, email, user, cenr, cea):
        self.email = email
        self.user = user
        self.cenr = cenr
        self.cea = cea


class SettableEnrollmentState(EmailEnrollmentState):
    """
    Settable enrollment state.
    Used for testing state changes.
    SettableEnrollmentState can be constructed and then
        a call to create_user will make objects which
        correspond to the state represented in the SettableEnrollmentState.
    """
    def __init__(self, user=False, enrollment=False, allowed=False, auto_enroll=False):  # pylint: disable=super-init-not-called
        self.user = user
        self.enrollment = enrollment
        self.allowed = allowed
        self.auto_enroll = auto_enroll

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __neq__(self, other):
        return not self == other

    def create_user(self, course_id=None):
        """
        Utility method to possibly create and possibly enroll a user.
        Creates a state matching the SettableEnrollmentState properties.
        Returns a tuple of (
            email,
            User, (optionally None)
            CourseEnrollment, (optionally None)
            CourseEnrollmentAllowed, (optionally None)
        )
        """
        # if self.user=False, then this will just be used to generate an email.
        email = "robot_no_user_exists_with_this_email@edx.org"
        if self.user:
            user = UserFactory()
            email = user.email
            if self.enrollment:
                cenr = CourseEnrollment.enroll(user, course_id)
                return EnrollmentObjects(email, user, cenr, None)
            else:
                return EnrollmentObjects(email, user, None, None)
        elif self.allowed:
            cea = CourseEnrollmentAllowed.objects.create(
                email=email,
                course_id=course_id,
                auto_enroll=self.auto_enroll,
            )
            return EnrollmentObjects(email, None, None, cea)
        else:
            return EnrollmentObjects(email, None, None, None)


@attr(shard=1)
class TestSendBetaRoleEmail(CacheIsolationTestCase):
    """
    Test edge cases for `send_beta_role_email`
    """

    def setUp(self):
        super(TestSendBetaRoleEmail, self).setUp()
        self.user = UserFactory.create()
        self.email_params = {'course': 'Robot Super Course'}

    def test_bad_action(self):
        bad_action = 'beta_tester'
        error_msg = "Unexpected action received '{}' - expected 'add' or 'remove'".format(bad_action)
        with self.assertRaisesRegexp(ValueError, error_msg):
            send_beta_role_email(bad_action, self.user, self.email_params)


@attr(shard=1)
class TestGetEmailParamsCCX(SharedModuleStoreTestCase):
    """
    Test what URLs the function get_email_params for CCX student enrollment.
    """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestGetEmailParamsCCX, cls).setUpClass()
        cls.course = CourseFactory.create()

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def setUp(self):
        super(TestGetEmailParamsCCX, self).setUp()
        self.coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.coach)
        self.ccx = CcxFactory(course_id=self.course.id, coach=self.coach)
        self.course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)

        # Explicitly construct what we expect the course URLs to be
        site = settings.SITE_NAME
        self.course_url = u'https://{}/courses/{}/'.format(
            site,
            self.course_key
        )
        self.course_about_url = self.course_url + 'about'
        self.registration_url = u'https://{}/register'.format(site)

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_ccx_enrollment_email_params(self):
        # For a CCX, what do we expect to get for the URLs?
        # Also make sure `auto_enroll` is properly passed through.
        result = get_email_params(
            self.course,
            True,
            course_key=self.course_key,
            display_name=self.ccx.display_name
        )

        self.assertEqual(result['display_name'], self.ccx.display_name)
        self.assertEqual(result['auto_enroll'], True)
        self.assertEqual(result['course_about_url'], self.course_about_url)
        self.assertEqual(result['registration_url'], self.registration_url)
        self.assertEqual(result['course_url'], self.course_url)


@attr(shard=1)
class TestGetEmailParams(SharedModuleStoreTestCase):
    """
    Test what URLs the function get_email_params returns under different
    production-like conditions.
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetEmailParams, cls).setUpClass()
        cls.course = CourseFactory.create()

        # Explicitly construct what we expect the course URLs to be
        site = settings.SITE_NAME
        cls.course_url = u'https://{}/courses/{}/'.format(
            site,
            cls.course.id.to_deprecated_string()
        )
        cls.course_about_url = cls.course_url + 'about'
        cls.registration_url = u'https://{}/register'.format(site)

    def setUp(self):
        super(TestGetEmailParams, self).setUp()

    def test_normal_params(self):
        # For a normal site, what do we expect to get for the URLs?
        # Also make sure `auto_enroll` is properly passed through.
        result = get_email_params(self.course, False)

        self.assertEqual(result['auto_enroll'], False)
        self.assertEqual(result['course_about_url'], self.course_about_url)
        self.assertEqual(result['registration_url'], self.registration_url)
        self.assertEqual(result['course_url'], self.course_url)

    def test_marketing_params(self):
        # For a site with a marketing front end, what do we expect to get for the URLs?
        # Also make sure `auto_enroll` is properly passed through.
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            result = get_email_params(self.course, True)

        self.assertEqual(result['auto_enroll'], True)
        # We should *not* get a course about url (LMS doesn't know what the marketing site URLs are)
        self.assertEqual(result['course_about_url'], None)
        self.assertEqual(result['registration_url'], self.registration_url)
        self.assertEqual(result['course_url'], self.course_url)


@attr(shard=1)
class TestRenderMessageToString(SharedModuleStoreTestCase):
    """
    Test that email templates can be rendered in a language chosen manually.
    Test CCX enrollmet email.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestRenderMessageToString, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.subject_template = 'emails/enroll_email_allowedsubject.txt'
        cls.message_template = 'emails/enroll_email_allowedmessage.txt'

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def setUp(self):
        super(TestRenderMessageToString, self).setUp()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=self.course.id, coach=coach)
        self.course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)

    def get_email_params(self):
        """
        Returns a dictionary of parameters used to render an email.
        """
        email_params = get_email_params(self.course, True)
        email_params["email_address"] = "user@example.com"
        email_params["full_name"] = "Jean Reno"

        return email_params

    def get_email_params_ccx(self):
        """
        Returns a dictionary of parameters used to render an email for CCX.
        """
        email_params = get_email_params(
            self.course,
            True,
            course_key=self.course_key,
            display_name=self.ccx.display_name
        )
        email_params["email_address"] = "user@example.com"
        email_params["full_name"] = "Jean Reno"

        return email_params

    def get_subject_and_message(self, language):
        """
        Returns the subject and message rendered in the specified language.
        """
        return render_message_to_string(
            self.subject_template,
            self.message_template,
            self.get_email_params(),
            language=language
        )

    def get_subject_and_message_ccx(self, subject_template, message_template):
        """
        Returns the subject and message rendered in the specified language for CCX.
        """
        return render_message_to_string(
            subject_template,
            message_template,
            self.get_email_params_ccx()
        )

    def test_subject_and_message_translation(self):
        subject, message = self.get_subject_and_message('fr')
        language_after_rendering = get_language()

        you_have_been_invited_in_french = u"Vous avez été invité"
        self.assertIn(you_have_been_invited_in_french, subject)
        self.assertIn(you_have_been_invited_in_french, message)
        self.assertEqual(settings.LANGUAGE_CODE, language_after_rendering)

    def test_platform_language_is_used_for_logged_in_user(self):
        with override_language('zh_CN'):    # simulate a user login
            subject, message = self.get_subject_and_message(None)
            self.assertIn("You have been", subject)
            self.assertIn("You have been", message)

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_render_enrollment_message_ccx_members(self):
        """
        Test enrollment email template renders for CCX.
        For EDX members.
        """
        subject_template = 'emails/enroll_email_enrolledsubject.txt'
        message_template = 'emails/enroll_email_enrolledmessage.txt'

        subject, message = self.get_subject_and_message_ccx(subject_template, message_template)
        self.assertIn(self.ccx.display_name, subject)
        self.assertIn(self.ccx.display_name, message)
        site = settings.SITE_NAME
        course_url = u'https://{}/courses/{}/'.format(
            site,
            self.course_key
        )
        self.assertIn(course_url, message)

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_render_unenrollment_message_ccx_members(self):
        """
        Test unenrollment email template renders for CCX.
        For EDX members.
        """
        subject_template = 'emails/unenroll_email_subject.txt'
        message_template = 'emails/unenroll_email_enrolledmessage.txt'

        subject, message = self.get_subject_and_message_ccx(subject_template, message_template)
        self.assertIn(self.ccx.display_name, subject)
        self.assertIn(self.ccx.display_name, message)

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_render_enrollment_message_ccx_non_members(self):
        """
        Test enrollment email template renders for CCX.
        For non EDX members.
        """
        subject_template = 'emails/enroll_email_allowedsubject.txt'
        message_template = 'emails/enroll_email_allowedmessage.txt'

        subject, message = self.get_subject_and_message_ccx(subject_template, message_template)
        self.assertIn(self.ccx.display_name, subject)
        self.assertIn(self.ccx.display_name, message)
        site = settings.SITE_NAME
        registration_url = u'https://{}/register'.format(site)
        self.assertIn(registration_url, message)

    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_render_unenrollment_message_ccx_non_members(self):
        """
        Test unenrollment email template renders for CCX.
        For non EDX members.
        """
        subject_template = 'emails/unenroll_email_subject.txt'
        message_template = 'emails/unenroll_email_allowedmessage.txt'

        subject, message = self.get_subject_and_message_ccx(subject_template, message_template)
        self.assertIn(self.ccx.display_name, subject)
        self.assertIn(self.ccx.display_name, message)
