'''
Unit tests for enrollment methods in views.py

'''

from django.test.utils import override_settings
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from courseware.access import _course_staff_group_name
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_XML_MODULESTORE, get_user
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from student.tests.factories import UserFactory, CourseEnrollmentFactory, UserProfileFactory, AdminFactory
from instructor.enrollment import enroll_emails, unenroll_emails, split_input_list


# @override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestInstructorEnrollsStudents(ModuleStoreTestCase):
    '''
    Check Enrollment/Unenrollment with/without auto-enrollment on activation

    Checks against database, not views or even return values of instructor.enrollment module
    '''

    def setUp(self):
        self.course = modulestore().get_course("edX/toy/2012_Fall")

        self.instructor = AdminFactory.create()

        def create_already_enrolled_student():
            user = UserFactory()
            ce = CourseEnrollment(course_id=self.course.id, user=user)
            ce.save()
            return user

        self.already_enrolled_students = [create_already_enrolled_student() for _ in xrange(5)]
        self.not_already_enrolled_students = [UserFactory() for _ in xrange(5)]

    def test_setup(self):
        '''Make sure setUp is working.'''

        self.assertEqual(
            CourseEnrollment.objects.filter(user__in=self.already_enrolled_students).count(),
            len(self.already_enrolled_students))
        self.assertEqual(
            CourseEnrollment.objects.filter(user__in=self.not_already_enrolled_students).count(),
            len(self.not_already_enrolled_students))

    # def setUp(self):

    #     self.full = modulestore().get_course("edX/full/6.002_Spring_2012")
    #     self.toy = modulestore().get_course("edX/toy/2012_Fall")

    #     #Create instructor and student accounts
    #     self.instructor = 'instructor1@test.com'
    #     self.password = 'foo'
    #     self.create_account('it1', self.instructor, self.password)
    #     self.activate_user(self.instructor)

    #     self.already_enrolled_emails = []
    #     for i in xrange(5):
    #         username = "already_enrolled_{}@test.com".format(i)
    #         email = "already_enrolled_{}@test.com".format(i)
    #         self.create_account(username, email, self.password)
    #         self.activate_user(email)
    #         self.already_enrolled_emails = email

    #         # enroll
    #         self.logout()
    #         self.login(email, self.password)
    #         self.enroll(self.toy)
    #         self.logout()

    #     self.not_already_enrolled_emails = []
    #     for i in xrange(5):
    #         username = "not_already_enrolled_{}@test.com".format(i)
    #         email = "not_already_enrolled_{}@test.com".format(i)
    #         self.create_account(username, email, self.password)
    #         self.activate_user(email)
    #         self.not_already_enrolled_emails = email

    #     def make_instructor(course):
    #         group_name = _course_staff_group_name(course.location)
    #         g = Group.objects.create(name=group_name)
    #         g.user_set.add(get_user(self.instructor))

    #     make_instructor(self.toy)

    #     # Enroll Instructor
    #     self.logout()
    #     self.login(self.instructor, self.password)
    #     self.enroll(self.toy)

    # def test_setup(self):
    #     self.assertEqual(
    #         CourseEnrollment.objects.filter(user__email__in=self.already_enrolled_emails).count(),
    #         len(self.already_enrolled_emails))
    #     self.assertEqual(
    #         CourseEnrollment.objects.filter(user__email__in=self.not_already_enrolled_emails).count(),
    #         len(self.not_already_enrolled_emails))

    # def test_enroll_one(self):
    #     course = self.toy

    #     enroll_emails(course.id, [self.student_email1])
    #     user = User.objects.get(email=self.student_email1)
    #     self.assertEqual(CourseEnrollment.objects.filter(course_id=course.id, user=user).count(), 1)


    # def test_unenrollment(self):
    #     '''
    #     Do un-enrollment test
    #     '''

    #     course = self.toy
    #     url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
    #     response = self.client.post(url, {'action': 'Unenroll multiple students', 'multiple_students': 'student1@test.com, student2@test.com'})

    #      #Check the page output
    #     self.assertContains(response, '<td>student1@test.com</td>')
    #     self.assertContains(response, '<td>student2@test.com</td>')
    #     self.assertContains(response, '<td>un-enrolled</td>')

    #     #Check the enrollment table
    #     user = User.objects.get(email='student1@test.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(0, len(ce))

    #     user = User.objects.get(email='student2@test.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(0, len(ce))

    # def test_enrollment_new_student_autoenroll_on(self):
    #     '''
    #     Do auto-enroll on test
    #     '''

    #     #Run the Enroll students command
    #     course = self.toy
    #     url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
    #     response = self.client.post(url, {'action': 'Enroll multiple students', 'multiple_students': 'test1_1@student.com, test1_2@student.com', 'auto_enroll': 'on'})

    #     #Check the page output
    #     self.assertContains(response, '<td>test1_1@student.com</td>')
    #     self.assertContains(response, '<td>test1_2@student.com</td>')
    #     self.assertContains(response, '<td>user does not exist, enrollment allowed, pending with auto enrollment on</td>')

    #     #Check the enrollmentallowed db entries
    #     cea = CourseEnrollmentAllowed.objects.filter(email='test1_1@student.com', course_id=course.id)
    #     self.assertEqual(1, cea[0].auto_enroll)
    #     cea = CourseEnrollmentAllowed.objects.filter(email='test1_2@student.com', course_id=course.id)
    #     self.assertEqual(1, cea[0].auto_enroll)

    #     #Check there is no enrollment db entry other than for the setup instructor and students
    #     ce = CourseEnrollment.objects.filter(course_id=course.id)
    #     self.assertEqual(3, len(ce))

    #     #Create and activate student accounts with same email
    #     self.student_email1 = 'test1_1@student.com'
    #     self.password = 'bar'
    #     self.create_account('s1_1', self.student_email1, self.password)
    #     self.activate_user(self.student_email1)

    #     self.student_email2 = 'test1_2@student.com'
    #     self.create_account('s1_2', self.student_email2, self.password)
    #     self.activate_user(self.student_email2)

    #     #Check students are enrolled
    #     user = User.objects.get(email='test1_1@student.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(1, len(ce))

    #     user = User.objects.get(email='test1_2@student.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(1, len(ce))

    # def test_enrollmemt_new_student_autoenroll_off(self):
    #     '''
    #     Do auto-enroll off test
    #     '''

    #     #Run the Enroll students command
    #     course = self.toy
    #     url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
    #     response = self.client.post(url, {'action': 'Enroll multiple students', 'multiple_students': 'test2_1@student.com, test2_2@student.com'})

    #     #Check the page output
    #     self.assertContains(response, '<td>test2_1@student.com</td>')
    #     self.assertContains(response, '<td>test2_2@student.com</td>')
    #     self.assertContains(response, '<td>user does not exist, enrollment allowed, pending with auto enrollment off</td>')

    #     #Check the enrollmentallowed db entries
    #     cea = CourseEnrollmentAllowed.objects.filter(email='test2_1@student.com', course_id=course.id)
    #     self.assertEqual(0, cea[0].auto_enroll)
    #     cea = CourseEnrollmentAllowed.objects.filter(email='test2_2@student.com', course_id=course.id)
    #     self.assertEqual(0, cea[0].auto_enroll)

    #     #Check there is no enrollment db entry other than for the setup instructor and students
    #     ce = CourseEnrollment.objects.filter(course_id=course.id)
    #     self.assertEqual(3, len(ce))

    #     #Create and activate student accounts with same email
    #     self.student = 'test2_1@student.com'
    #     self.password = 'bar'
    #     self.create_account('s2_1', self.student, self.password)
    #     self.activate_user(self.student)

    #     self.student = 'test2_2@student.com'
    #     self.create_account('s2_2', self.student, self.password)
    #     self.activate_user(self.student)

    #     #Check students are not enrolled
    #     user = User.objects.get(email='test2_1@student.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(0, len(ce))
    #     user = User.objects.get(email='test2_2@student.com')
    #     ce = CourseEnrollment.objects.filter(course_id=course.id, user=user)
    #     self.assertEqual(0, len(ce))

    # def test_get_and_clean_student_list(self):
    #     '''
    #     Clean user input test
    #     '''

    #     string = "abc@test.com, def@test.com ghi@test.com \n \n jkl@test.com      "
    #     cleaned_string, cleaned_string_lc = get_and_clean_student_list(string)
    #     self.assertEqual(cleaned_string, ['abc@test.com', 'def@test.com', 'ghi@test.com', 'jkl@test.com'])
