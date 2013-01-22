import logging
from mock import MagicMock, patch
import datetime

from django.test import TestCase
from django.http import Http404 
from django.conf import settings
from django.test.utils import override_settings
from django.contrib.auth.models import User

from student.models import CourseEnrollment
import courseware.views as views
from xmodule.modulestore.django import modulestore


class Stub():
    pass

class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='dummy', password='123456',
                                        email='test@mit.edu')
        self.date = datetime.datetime(2013,1,22)
        self.course_id = 'edx/toy/Fall_2012'
        self.enrollment = CourseEnrollment.objects.get_or_create(user = self.user,
                                                  course_id = self.course_id,
                                                  created = self.date)[0]

    def test_user_groups(self):
        # depreciated function?
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertEquals(views.user_groups(mock_user),[])
        

    @override_settings(DEBUG = True)
    def test_user_groups_debug(self):
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = True
        pass
        #views.user_groups(mock_user)
        #Keep going later

    def test_get_current_child(self):
        self.assertIsNone(views.get_current_child(Stub()))
        mock_xmodule = MagicMock()
        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one','two']
        self.assertEquals(views.get_current_child(mock_xmodule), 'one')
        mock_xmodule_2 = MagicMock()
        mock_xmodule_2.position = 3
        mock_xmodule_2.get_display_items.return_value = []
        self.assertIsNone(views.get_current_child(mock_xmodule_2))

    def test_redirect_to_course_position(self):
        mock_module = MagicMock()
        mock_module.descriptor.id = 'Underwater Basketweaving'
        mock_module.position = 3
        mock_module.get_display_items.return_value = []
        self.assertRaises(Http404, views.redirect_to_course_position,
                          mock_module, True)

    def test_index(self):
        print modulestore()
        assert False

    def test_registered_for_course(self):
        self.assertFalse(views.registered_for_course('Basketweaving', None))
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertFalse(views.registered_for_course('dummy', mock_user))
        mock_course = MagicMock()
        mock_course.id = self.course_id
        self.assertTrue(views.registered_for_course(mock_course, self.user))
