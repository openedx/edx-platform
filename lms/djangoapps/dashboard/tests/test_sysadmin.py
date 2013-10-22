import unittest

from django.test.client import Client
from django.test import TestCase
from django.test.utils import override_settings

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

class TestDefaultView(TestCase):
    """
    Check that landing page is the status page
    """

    def setUp(self):
        
        self.user = User.objects.create_user('test_user', 'test_user+sysadmin@edx.org', 'foo')
        self.c = Client()
    
    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_staff_access(self):

        response = self.c.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])
    
        response = self.c.get(reverse('gitlogs'))
        self.assertEqual('/gitlogs', response.context['next'])

        li = self.c.login(username=self.user.username,
                     password='foo')
        self.assertTrue(li)

        response = self.c.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])
    
        response = self.c.get(reverse('gitlogs'))
        self.assertEqual('/gitlogs', response.context['next'])

        self.user.is_staff = True
        self.user.save()
        
        self.c.logout()
        self.c.login(username=self.user.username, password='foo')

        response = self.c.get(reverse('sysadmin'))
        self.assertFalse(hasattr(response.context, 'next'))
    
        response = self.c.get(reverse('gitlogs'))
        self.assertFalse(hasattr(response.context, 'next'))
        
    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_user_mod(self):
        """Create and delete a user"""

        self.user.is_staff = True
        self.user.save()
        
        self.c.logout()
        self.c.login(username=self.user.username, password='foo')

        # Create user
        self.c.post(reverse('sysadmin'),
                    {'dash_mode': _('Status'), 
                     'action': _('Create user'),
                     'student_uname': 'test_cuser+sysadmin@edx.org',
                     'student_fullname': 'test cuser',
                     'student_password': 'foozor' })
    
        self.assertIsNotNone(
            User.objects.get(username='test_cuser+sysadmin@edx.org', 
                             email='test_cuser+sysadmin@edx.org'))

        # login as new user to confirm
        self.assertTrue(self.c.login(username='test_cuser+sysadmin@edx.org', 
                                     password='foozor'))

        self.c.logout()
        self.c.login(username=self.user.username, password='foo')

        # Delete user
        response = self.c.post(reverse('sysadmin'),
                               { 'dash_mode': _('Status'), 
                                 'action': _('Delete user'),
                                 'student_uname': 'test_cuser+sysadmin@edx.org',
                                 'student_fullname': 'test cuser',})
        
        self.assertEqual(0,len(User.objects.filter(
            username='test_cuser+sysadmin@edx.org', 
            email='test_cuser+sysadmin@edx.org')))

        self.assertEqual(1, len(User.objects.all()))
        
    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_user_csv(self):
        """Download and validate CSV"""

        self.user.is_staff = True
        self.user.save()

        self.assertTrue(self.c.login(username=self.user.username, password='foo'))

        response = self.c.post(reverse('sysadmin'), {'dash_mode': _('Status'), 
                     'action': _('Download list of all users (csv file)'),})

        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual('text/csv', response['Content-Type'])
        self.assertIn('test_user', response.content)
        self.assertTrue(2, len(response.content.splitlines()))

