"""
Unit tests for instructor.enrollment methods.
"""

import json
from abc import ABCMeta
from django.contrib.auth.models import User
from courseware.models import StudentModule
from django.test import TestCase
from student.tests.factories import UserFactory

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from instructor.enrollment import (EmailEnrollmentState,
                                   enroll_email, unenroll_email,
                                   reset_student_attempts)


class TestSettableEnrollmentState(TestCase):
    """ Test the basis class for enrollment tests. """
    def setUp(self):
        self.course_id = 'robot:/a/fake/c::rse/id'

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
        eobjs = mes.create_user(self.course_id)
        ees = EmailEnrollmentState(self.course_id, eobjs.email)
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
        self.course_id = 'robot:/a/fake/c::rse/id'

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
        eobjs = before_ideal.create_user(self.course_id)
        before = EmailEnrollmentState(self.course_id, eobjs.email)
        self.assertEqual(before, before_ideal)

        # do action
        print "running action..."
        action(eobjs.email)

        # check after
        print "checking effects..."
        after = EmailEnrollmentState(self.course_id, eobjs.email)
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

        action = lambda email: enroll_email(self.course_id, email)

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

        action = lambda email: enroll_email(self.course_id, email)

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

        action = lambda email: enroll_email(self.course_id, email)

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

        action = lambda email: enroll_email(self.course_id, email)

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

        action = lambda email: enroll_email(self.course_id, email, auto_enroll=True)

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

        action = lambda email: enroll_email(self.course_id, email, auto_enroll=False)

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

        action = lambda email: unenroll_email(self.course_id, email)

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

        action = lambda email: unenroll_email(self.course_id, email)

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

        action = lambda email: unenroll_email(self.course_id, email)

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

        action = lambda email: unenroll_email(self.course_id, email)

        return self._run_state_change_test(before_ideal, after_ideal, action)


class TestInstructorEnrollmentStudentModule(TestCase):
    """ Test student module manipulations. """
    def setUp(self):
        self.course_id = 'robot:/a/fake/c::rse/id'

    def test_reset_student_attempts(self):
        user = UserFactory()
        msk = 'robot/module/state/key'
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        module = StudentModule.objects.create(student=user, course_id=self.course_id, module_state_key=msk, state=original_state)
        # lambda to reload the module state from the database
        module = lambda: StudentModule.objects.get(student=user, course_id=self.course_id, module_state_key=msk)
        self.assertEqual(json.loads(module().state)['attempts'], 32)
        reset_student_attempts(self.course_id, user, msk)
        self.assertEqual(json.loads(module().state)['attempts'], 0)

    def test_delete_student_attempts(self):
        user = UserFactory()
        msk = 'robot/module/state/key'
        original_state = json.dumps({'attempts': 32, 'otherstuff': 'alsorobots'})
        StudentModule.objects.create(student=user, course_id=self.course_id, module_state_key=msk, state=original_state)
        self.assertEqual(StudentModule.objects.filter(student=user, course_id=self.course_id, module_state_key=msk).count(), 1)
        reset_student_attempts(self.course_id, user, msk, delete_module=True)
        self.assertEqual(StudentModule.objects.filter(student=user, course_id=self.course_id, module_state_key=msk).count(), 0)


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
                cenr = CourseEnrollment.objects.create(
                    user=user,
                    course_id=course_id
                )
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
