<<<<<<< HEAD
'''
Unit tests for enrollment methods in views.py

'''

from django.test.utils import override_settings
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from courseware.access import _course_staff_group_name
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_XML_MODULESTORE, get_user
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from instructor.views import get_and_clean_student_list
from django.test import TestCase
from student.tests.factories import UserFactory

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from instructor.enrollment import enroll_emails, unenroll_emails, split_input_list


class TestInstructorEnrollmentDB(TestCase):
    '''Test instructor enrollment administration against database effects'''
    def setUp(self):
        self.course = MockCourse('jus:/a/fake/c::rse/id')

    def test_split_input_list(self):
        strings = []
        lists = []
        strings.append("Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed")
        lists.append(['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus', 'ut@lacinia.Sed'])

        for (s, l) in zip(strings, lists):
            self.assertEqual(split_input_list(s), l)

    def test_enroll_emails_userexists_alreadyenrolled(self):
        user = UserFactory()
        ce = CourseEnrollment(course_id=self.course.course_id, user=user)
        ce.save()

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=user.email).count(), 1)

        enroll_emails(self.course.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=user.email).count(), 1)

    def test_enroll_emails_userexists_succeedenrolling(self):
        user = UserFactory()

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=user.email).count(), 0)

        enroll_emails(self.course.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=user.email).count(), 1)

    def test_enroll_emails_nouser_alreadyallowed(self):
        email_without_user = 'test_enroll_emails_nouser_alreadyallowed@test.org'

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 0)

        cea = CourseEnrollmentAllowed(course_id=self.course.course_id, email=email_without_user, auto_enroll=False)
        cea.save()

        enroll_emails(self.course.course_id, [email_without_user])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 1)
        self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course.course_id, email=email_without_user).auto_enroll, False)

    def test_enroll_emails_nouser_suceedallow(self):
        email_without_user = 'test_enroll_emails_nouser_suceedallow@test.org'

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 0)

        enroll_emails(self.course.course_id, [email_without_user])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 1)
        self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course.course_id, email=email_without_user).auto_enroll, False)

    def test_enroll_multiple(self):
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        email_without_user1 = 'test_enroll_emails_nouser_suceedallow_1@test.org'
        email_without_user2 = 'test_enroll_emails_nouser_suceedallow_2@test.org'
        email_without_user3 = 'test_enroll_emails_nouser_suceedallow_3@test.org'

        def test_db(auto_enroll):
            for user in [user1, user2, user3]:
                self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user=user).count(), 1)
                self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=user.email).count(), 0)

            for email in [email_without_user1, email_without_user2, email_without_user3]:
                self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email).count(), 0)
                self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email).count(), 1)
                self.assertEqual(CourseEnrollmentAllowed.objects.get(course_id=self.course.course_id, email=email).auto_enroll, auto_enroll)

        enroll_emails(self.course.course_id, [user1.email, user2.email, user3.email, email_without_user1, email_without_user2, email_without_user3], auto_enroll=True)
        test_db(True)
        enroll_emails(self.course.course_id, [user1.email, user2.email, user3.email, email_without_user1, email_without_user2, email_without_user3], auto_enroll=False)
        test_db(False)

    def test_unenroll_alreadyallowed(self):
        email_without_user = 'test_unenroll_alreadyallowed@test.org'
        cea = CourseEnrollmentAllowed(course_id=self.course.course_id, email=email_without_user, auto_enroll=False)
        cea.save()

        unenroll_emails(self.course.course_id, [email_without_user])

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 0)

    def test_unenroll_alreadyenrolled(self):
        user = UserFactory()
        ce = CourseEnrollment(course_id=self.course.course_id, user=user)
        ce.save()

        unenroll_emails(self.course.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user=user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=user.email).count(), 0)

    def test_unenroll_notenrolled(self):
        user = UserFactory()

        unenroll_emails(self.course.course_id, [user.email])

        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user=user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=user.email).count(), 0)

    def test_unenroll_nosuchuser(self):
        email_without_user = 'test_unenroll_nosuchuser@test.org'

        unenroll_emails(self.course.course_id, [email_without_user])

        self.assertEqual(User.objects.filter(email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course.course_id, user__email=email_without_user).count(), 0)
        self.assertEqual(CourseEnrollmentAllowed.objects.filter(course_id=self.course.course_id, email=email_without_user).count(), 0)


class MockCourse(object):
    def __init__(self, course_id):
        self.course_id = course_id
