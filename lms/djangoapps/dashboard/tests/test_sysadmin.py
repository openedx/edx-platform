"""
Provide tests for sysadmin dashboard feature in sysadmin.py
"""

import unittest
import os

from django.test.client import Client
from django.test.utils import override_settings

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from dashboard.sysadmin import create_user
from external_auth.models import ExternalAuthMap
from django.contrib.auth.hashers import check_password
from xmodule.modulestore.django import modulestore
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

TEST_MONGODB_LOG = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'db': 'test_xlog',
}


@override_settings(MONGODB_LOG=TEST_MONGODB_LOG)
class TestSysadmin(ModuleStoreTestCase):
    """
    Check that landing page is the status page
    """

    def setUp(self):
        super(TestSysadmin, self).setUp()
        self.user = User.objects.create_user('test_user', 'test_user+sysadmin@edx.org', 'foo')
        self.client = Client()

    def _setstaff_login(self):
        """ Makes the test user staff and logs them in"""

        self.user.is_staff = True
        self.user.save()
        self.client.login(username=self.user.username, password='foo')

    def _add_edx4edx(self):
        """Adds the edx4edx sample course"""

        return self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Courses'),
            'repo_location': 'https://github.com/mitocw/edx4edx_lite.git',
            'action': _('Load new course from github'), })

    def _rm_edx4edx(self):
        """Deletes the sample course from the XML store"""
        # pylint: disable-msg=E1103

        def_ms = modulestore()
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(os.path.abspath(settings.DATA_DIR)), None)

        # Delete git loaded course
        return self.client.post(reverse('sysadmin'),
                                {'dash_mode': _('Courses'),
                                 'course_id': course.id,
                                 'action': _('Delete course from site'), })

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_staff_access(self):
        # pylint: disable-msg=E1103

        response = self.client.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])

        response = self.client.get(reverse('gitlogs'))
        self.assertEqual('/gitlogs', response.context['next'])

        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        response = self.client.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])

        response = self.client.get(reverse('gitlogs'))
        self.assertEqual('/gitlogs', response.context['next'])

        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.login(username=self.user.username, password='foo')

        response = self.client.get(reverse('sysadmin'))
        self.assertFalse(hasattr(response.context, 'next'))

        response = self.client.get(reverse('gitlogs'))
        self.assertFalse(hasattr(response.context, 'next'))

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_user_mod(self):
        """Create and delete a user"""

        self._setstaff_login()

        self.client.login(username=self.user.username, password='foo')

        # Create user
        self.client.post(reverse('sysadmin'),
                         {'dash_mode': _('Status'),
                          'action': _('Create user'),
                          'student_uname': 'test_cuser+sysadmin@edx.org',
                          'student_fullname': 'test cuser',
                          'student_password': 'foozor', })

        self.assertIsNotNone(
            User.objects.get(username='test_cuser+sysadmin@edx.org',
                             email='test_cuser+sysadmin@edx.org'))

        # login as new user to confirm
        self.assertTrue(self.client.login(username='test_cuser+sysadmin@edx.org',
                                          password='foozor'))

        self.client.logout()
        self.client.login(username=self.user.username, password='foo')

        # Delete user
        self.client.post(reverse('sysadmin'),
                         {'dash_mode': _('Status'),
                          'action': _('Delete user'),
                          'student_uname': 'test_cuser+sysadmin@edx.org',
                          'student_fullname': 'test cuser', })

        self.assertEqual(0, len(User.objects.filter(
            username='test_cuser+sysadmin@edx.org',
            email='test_cuser+sysadmin@edx.org')))

        self.assertEqual(1, len(User.objects.all()))

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_user_csv(self):
        """Download and validate user CSV"""

        self._setstaff_login()

        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Status'),
            'action': _('Download list of all users (csv file)'),
        })

        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual('text/csv', response['Content-Type'])
        self.assertIn('test_user', response.content)
        self.assertTrue(2, len(response.content.splitlines()))

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_authmap_repair(self):
        """Run authmap check and repair"""

        self._setstaff_login()

        create_user('test0', 'test test', do_mit=True)
        # Will raise exception, so no assert needed
        eamap = ExternalAuthMap.objects.get(external_name='test test')
        mitu = User.objects.get(username='test0')

        self.assertTrue(check_password(eamap.internal_password, mitu.password))

        mitu.set_password('not autogenerated')
        mitu.save()

        self.assertFalse(check_password(eamap.internal_password, mitu.password))

        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Status'),
            'action': _('Check and repair external Auth Map'), })

        self.assertIn('{0} test0'.format(_('Failed in authenticating')), response.content)
        self.assertIn(_('fixed password'), response.content)

        self.assertTrue(self.client.login(username='test0', password=eamap.internal_password))

        # Check for all OK
        self._setstaff_login()
        response = self.client.post(reverse('sysadmin'),
                                    {'dash_mode': _('Status'),
                                     'action': _('Check and repair external Auth Map'), })
        self.assertIn(_('All ok!'), response.content)

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_xml_course_add_delete(self):
        """add and delete course from xml module store"""

        self._setstaff_login()

        # Try bad git repo
        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Courses'),
            'repo_location': 'github.com/mitocw/edx4edx_lite',
            'action': _('Load new course from github'), })
        self.assertIn(_("The git repo location should end with '.git', and be a valid url"), response.content.decode('utf-8'))

        # Create git loaded course
        response = self._add_edx4edx()

        def_ms = modulestore()
        self.assertIn('xml', str(def_ms.__class__))
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR)), None)
        self.assertIsNotNone(course)

        response = self._rm_edx4edx()
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR)), None)
        self.assertIsNone(course)

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_git_pull(self):
        """Make sure we can pull"""

        self._setstaff_login()

        response = self._add_edx4edx()
        response = self._add_edx4edx()
        self.assertIn(_("The course {0} already exists in the data directory! "
                        "(reloading anyway)").format('edx4edx_lite'),
                      response.content.decode('utf-8'))
        self._rm_edx4edx()

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_staff_csv(self):
        """Download and validate staff CSV"""

        self._setstaff_login()
        self._add_edx4edx()

        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Staffing and Enrollment'),
            'action': _('Download staff and instructor list (csv file)'),
        })

        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual('text/csv', response['Content-Type'])
        columns = [_('course_id'), _('role'), _('username'), _('email'), _('full_name'), ]
        self.assertIn(','.join('"' + c + '"' for c in columns), response.content)

        self._rm_edx4edx()

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_enrollment_page(self):
        """
        Adds a course and makes sure that it shows up on the staffing and
        enrollment page
        """

        self._setstaff_login()
        self._add_edx4edx()
        response = self.client.post(reverse('sysadmin'), {'dash_mode': _('Staffing and Enrollment')})
        print(response.content)
        self.assertIn('edx4edx', response.content)
        self._rm_edx4edx()

    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_gitlogs(self):
        self._setstaff_login()

        response = self.client.get(reverse('gitlogs'))
        # Check that our earlier import has a log with a link to details
        self.assertIn('/gitlogs/MITx/edx4edx/edx4edx', response.content)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={'course_id': 'MITx/edx4edx/edx4edx'}))

        self.assertIn('======&gt; IMPORTING course to location', response.content)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
@override_settings(MONGODB_LOG=TEST_MONGODB_LOG)
class TestSysAdminMongoCourseImport(ModuleStoreTestCase):
    """
    Check that importing into the mongo module store works
    """

    def setUp(self):
        super(TestSysAdminMongoCourseImport, self).setUp()
        self.user = User.objects.create_user('test_user', 'test_user+sysadmin@edx.org', 'foo')
        self.client = Client()

    def _setstaff_login(self):
        """ Makes the test user staff and logs them in"""

        self.user.is_staff = True
        self.user.save()

        self.client.login(username=self.user.username, password='foo')

    @override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_mongo_course_add_delete(self):
        """same as TestSysadmin.test_xml_course_add_delete, but use mongo store"""

        self._setstaff_login()
        def_ms = modulestore()
        self.assertIn('mongo', str(def_ms.__class__))

        # Create git loaded course
        self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Courses'),
            'repo_location': 'https://github.com/mitocw/edx4edx_lite.git',
            'action': _('Load new course from github'), })

        course = def_ms.get_course('MITx/edx4edx/edx4edx')
        self.assertIsNotNone(course)

        # Delete git loaded course
        self.client.post(reverse('sysadmin'),
                         {'dash_mode': _('Courses'),
                          'course_id': course.id,
                          'action': _('Delete course from site'), })
        course = def_ms.get_course('MITx/edx4edx/edx4edx')
        self.assertIsNone(course)

    @override_settings(GIT_ADD_COURSE_SCRIPT='')
    @unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
    def test_no_script_set(self):
        """ Test if settings are right on mongo store import"""

        self._setstaff_login()

        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Courses'),
            'repo_location': 'https://github.com/mitocw/edx4edx_lite.git',
            'action': _('Load new course from github'), })
        self.assertIn(_('Must configure GIT_ADD_COURSE_SCRIPT in settings first!'),
                      response.content)
