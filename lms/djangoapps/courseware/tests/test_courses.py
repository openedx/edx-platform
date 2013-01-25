from mock import MagicMock, patch
import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from django.test.utils import override_settings

from student.models import CourseEnrollment
import courseware.courses as courses
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.django import modulestore

def xml_store_config(data_dir):
    return {
    'default': {
        'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
        'OPTIONS': {
            'data_dir': data_dir,
            'default_class': 'xmodule.hidden_module.HiddenDescriptor',
        }
    }
}

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class CoursesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='dummy', password='123456',
                                        email='test@mit.edu')
        self.date = datetime.datetime(2013,1,22)
        self.course_id = 'edx/toy/2012_Fall'
        self.enrollment = CourseEnrollment.objects.get_or_create(user = self.user,
                                                  course_id = self.course_id,
                                                  created = self.date)[0]
        self._MODULESTORES = {}
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')
    
    def test_get_course_by_id(self):
        courses.get_course_by_id("edx/toy/2012_Fall")

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class CoursesTests(TestCase):
    def setUp(self):
        self._MODULESTORES = {}
        self.course_name = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')
        self.fake_user = User.objects.create(is_superuser=True)

        '''
        no test written for get_request_for_thread
        '''

    def test_get_course_by_id(self):
        self.test_course_id = "edX/toy/2012_Fall"
        # print modulestore().get_instance(test_course_id, Location('i4x', 'edx', 'toy', 'course', '2012_Fall'))
        self.assertEqual(courses.get_course_by_id(self.test_course_id),modulestore().get_instance(self.test_course_id, Location('i4x', 'edX', 'toy', 'course', '2012_Fall'), None))


