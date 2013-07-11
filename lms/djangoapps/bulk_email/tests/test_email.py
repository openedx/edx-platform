"""
Unit tests for sending course email
"""

from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, GroupFactory, CourseEnrollmentFactory
from django.core import mail

STAFF_COUNT = 3
STUDENT_COUNT = 10

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmail(ModuleStoreTestCase):
    def setUp(self):
        """
        Makes a course, which will be the same for all tests.
        """
        self.course = CourseFactory.create()
        self.instructor = UserFactory.create(username="instructor", email="robot+instructor@edx.org")
        #Create instructor group for course
        g = GroupFactory.create(name="instructor_MITx/999/Robot_Super_Course")
        g.user_set.add(self.instructor)

        #create staff
        self.staff = [UserFactory() for _ in xrange(STAFF_COUNT)]
        g = GroupFactory()
        for staff in self.staff:
            g.user_set.add(staff)

        #create students
        self.students = [UserFactory() for _ in xrange(STUDENT_COUNT)]
        for student in self.students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        self.client.login(username=self.instructor.username, password="test")
        
    def test_send_to_self(self):
        """
        Make sure email send to myself goes to myself.
        """
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.post(url, {'action': 'Send email', 'to': 'myself', 'subject': 'test subject for myself', 'message': 'test message for myself'})

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.instructor.email)
        self.assertEquals(mail.outbox[0].subject, '[' + self.course.display_name + ']' + ' test subject for myself')

    def test_send_to_staff(self):
        """
        Make sure email send to staff and instructors goes there.
        """
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.post(url, {'action': 'Send email', 'to': 'staff', 'subject': 'test subject for staff', 'message': 'test message for subject'})

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1+len(self.staff))
        self.assertItemsEqual([e.to[0] for e in mail.outbox], [self.instructor.email]+[s.email for s in self.staff])

    def test_send_to_all(self):
        """
        Make sure email send to all goes there.
        """
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.post(url, {'action': 'Send email', 'to': 'all', 'subject': 'test subject for all', 'message': 'test message for all'})

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1+len(self.staff)+len(self.students))
        self.assertItemsEqual([e.to[0] for e in mail.outbox], [self.instructor.email]+[s.email for s in self.staff]+[s.email for s in self.students])
