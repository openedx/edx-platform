"""
Unit tests for email feature in instructor dashboard

Based on (and depends on) unit tests for courseware.
"""

from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from django.contrib.auth.models import Group

from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.access import _course_staff_group_name
from courseware.tests.tests import LoginEnrollmentTestCase, TEST_DATA_XML_MODULESTORE, get_user
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardEmailView(LoginEnrollmentTestCase):
    '''
    Check for email view displayed with flag
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        
        self.toy = modulestore().get_course("edX/toy/2012_Fall")
        
        # Create instructor account
        self.instructor = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.instructor, self.password)
        self.activate_user(self.instructor)

        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(get_user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)

    def test_email_flag_true(self):
        oldEmailFlag = settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL']
        settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True
        response = self.client.get(reverse('instructor_dashboard',
                                   kwargs={'course_id': self.toy.id}))
        email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'
        self.assertTrue(email_link in response.content)

        session = self.client.session
        session['idash_mode'] = 'Email'
        session.save()
        response = self.client.get(reverse('instructor_dashboard',
                                   kwargs={'course_id': self.toy.id}))
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)
        send_to_label = '<label for="id_to">Send to:</label>'
        self.assertTrue(send_to_label in response.content)

        del self.client.session['idash_mode']
        settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = oldEmailFlag

    def test_email_flag_false(self):
        oldEmailFlag = settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL']
        settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = False
        response = self.client.get(reverse('instructor_dashboard',
                                   kwargs={'course_id': self.toy.id}))
        email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'
        self.assertFalse(email_link in response.content)
        
        settings.MITX_FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = oldEmailFlag
