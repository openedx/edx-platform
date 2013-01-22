from mock import MagicMock, patch
import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from student.models import CourseEnrollment
import courseware.courses as courses

class CoursesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='dummy', password='123456',
                                        email='test@mit.edu')
        self.date = datetime.datetime(2013,1,22)
        self.course_id = 'edx/toy/Fall_2012'
        self.enrollment = CourseEnrollment.objects.get_or_create(user = self.user,
                                                  course_id = self.course_id,
                                                  created = self.date)[0]
    
    def test_get_course_by_id(self):
        courses.get_course_by_id(self.course_id)
