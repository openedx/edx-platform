"""
Unit tests for instructor.enrollment methods.
"""

import json
from django.contrib.auth.models import User
from courseware.models import StudentModule
from django.test import TestCase
from student.tests.factories import UserFactory

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from instructor.enrollment import (enroll_emails, unenroll_emails,
                                   split_input_list, reset_student_attempts)


class TestInstructorEnrollmentDB(TestCase):
    '''Test instructor enrollment administration against database effects'''
    def setUp(self):
        self.course_id = 'robot:/a/fake/c::rse/id'

    def test_split_input_list(self):
        strings = []
        lists = []
        strings.append("Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed")
        lists.append(['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus', 'ut@lacinia.Sed'])

        for (stng, lst) in zip(strings, lists):
            self.assertEqual(split_input_list(stng), lst)

    def test_enroll_emails_userexists_alreadyenrolled(self):
        user = UserFactory()
        cenr = CourseEnrollment(course_id=self.course_id, user=user)
        cenr.save()

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=user.email).count(), 1)

        enroll_emails(self.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=user.email).count(), 1)

    def test_enroll_emails_userexists_succeedenrolling(self):
        user = UserFactory()

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=user.email).count(), 0)

        enroll_emails(self.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=user.email).count(), 1)

    def test_enroll_emails_nouser_alreadyallowed(self):
        email_without_user = 'robot_enroll_emails_nouser_alreadyallowed@test.org'

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 0)

        cea = CourseEnrollmentAllowed(course_id=self.course_id, email=email_without_user, auto_enroll=False)
        cea.save()

        enroll_emails(self.course_id, [email_without_user])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 1)
        self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course_id, email=email_without_user).auto_enroll, False)

    def test_enroll_emails_nouser_suceedallow(self):
        email_without_user = 'robot_enroll_emails_nouser_suceedallow@test.org'

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 0)

        enroll_emails(self.course_id, [email_without_user])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 1)
        self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course_id, email=email_without_user).auto_enroll, False)

    def test_enroll_multiple(self):
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        email_without_user1 = 'robot_enroll_emails_nouser_suceedallow_1@test.org'
        email_without_user2 = 'robot_enroll_emails_nouser_suceedallow_2@test.org'
        email_without_user3 = 'robot_enroll_emails_nouser_suceedallow_3@test.org'

        def test_db(auto_enroll):
            for user in [user1, user2, user3]:
                self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user=user).count(), 1)
                self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=user.email).count(), 0)

            for email in [email_without_user1, email_without_user2, email_without_user3]:
                self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email).count(), 0)
                self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email).count(), 1)
                self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course_id, email=email).auto_enroll, auto_enroll)

        enroll_emails(self.course_id, [user1.email, user2.email, user3.email, email_without_user1, email_without_user2, email_without_user3], auto_enroll=True)
        test_db(True)
        enroll_emails(self.course_id, [user1.email, user2.email, user3.email, email_without_user1, email_without_user2, email_without_user3], auto_enroll=False)
        test_db(False)

    def test_unenroll_alreadyallowed(self):
        email_without_user = 'robot_unenroll_alreadyallowed@test.org'
        cea = CourseEnrollmentAllowed(course_id=self.course_id, email=email_without_user, auto_enroll=False)
        cea.save()

        unenroll_emails(self.course_id, [email_without_user])

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 0)

    def test_unenroll_alreadyenrolled(self):
        user = UserFactory()
        cenr = CourseEnrollment(course_id=self.course_id, user=user)
        cenr.save()

        unenroll_emails(self.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user=user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=user.email).count(), 0)

    def test_unenroll_notenrolled(self):
        user = UserFactory()

        unenroll_emails(self.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user=user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=user.email).count(), 0)

    def test_unenroll_nosuchuser(self):
        email_without_user = 'robot_unenroll_nosuchuser@test.org'

        unenroll_emails(self.course_id, [email_without_user])

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course_id, email=email_without_user).count(), 0)

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
