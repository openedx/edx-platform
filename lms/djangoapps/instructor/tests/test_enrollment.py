"""
Unit tests for instructor.enrollment methods.
"""

import json
import mock
from abc import ABCMeta
from courseware.models import StudentModule
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from instructor.enrollment import (
    EmailEnrollmentState,
    enroll_email,
    get_email_params,
    reset_student_attempts,
    send_beta_role_email,
    unenroll_email
)
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from submissions import api as sub_api
from student.models import anonymous_id_for_user
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestSettableEnrollmentState(TestCase):
    """ Test the basis class for enrollment tests. """
    def setUp(self):
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


class TestEnrollmentChangeBase(TestCase):
    """
    Test instructor enrollment administration against database effects.

    Test methods in derived classes follow a strict format.
    `action` is a function which is run
    the test will pass if `action` mutates state from `before_ideal` to `after_ideal`
    """

    __metaclass__ = ABCMeta

    def setUp(self):
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


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorEnrollmentStudentModule(TestCase):
    """ Test student module manipulations. """
    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('fake', 'course', 'id')

    def test_reset_student_attempts(self):
        user = UserFactory()
        msk = self.course_key.make_usage_key('dummy', 'module')
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        StudentModule.objects.create(student=user, course_id=self.course_key, module_state_key=msk, state=original_state)
        # lambda to reload the module state from the database
        module = lambda: StudentModule.objects.get(student=user, course_id=self.course_key, module_state_key=msk)
        self.assertEqual(json.loads(module().state)['attempts'], 32)
        reset_student_attempts(self.course_key, user, msk)
        self.assertEqual(json.loads(module().state)['attempts'], 0)

    def test_delete_student_attempts(self):
        user = UserFactory()
        msk = self.course_key.make_usage_key('dummy', 'module')
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        StudentModule.objects.create(student=user, course_id=self.course_key, module_state_key=msk, state=original_state)
        self.assertEqual(StudentModule.objects.filter(student=user, course_id=self.course_key, module_state_key=msk).count(), 1)
        reset_student_attempts(self.course_key, user, msk, delete_module=True)
        self.assertEqual(StudentModule.objects.filter(student=user, course_id=self.course_key, module_state_key=msk).count(), 0)

    def test_delete_submission_scores(self):
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
            delete_module=True
        )

        # Verify that the student's scores have been reset in the submissions API
        score = sub_api.get_score(student_item)
        self.assertIs(score, None)


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
    def __init__(self, user=False, enrollment=False, allowed=False, auto_enroll=False):  # pylint: disable=W0231
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


class TestSendBetaRoleEmail(TestCase):
    """
    Test edge cases for `send_beta_role_email`
    """

    def setUp(self):
        self.user = UserFactory.create()
        self.email_params = {'course': 'Robot Super Course'}

    def test_bad_action(self):
        bad_action = 'beta_tester'
        error_msg = "Unexpected action received '{}' - expected 'add' or 'remove'".format(bad_action)
        with self.assertRaisesRegexp(ValueError, error_msg):
            send_beta_role_email(bad_action, self.user, self.email_params)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestGetEmailParams(ModuleStoreTestCase):
    """
    Test what URLs the function get_email_params returns under different
    production-like conditions.
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Explicitly construct what we expect the course URLs to be
        site = settings.SITE_NAME
        self.course_url = u'https://{}/courses/{}/'.format(
            site,
            self.course.id.to_deprecated_string()
        )
        self.course_about_url = self.course_url + 'about'
        self.registration_url = u'https://{}/register'.format(
            site,
        )

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
