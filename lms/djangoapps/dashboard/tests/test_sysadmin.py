"""
Provide tests for sysadmin dashboard feature in sysadmin.py
"""

import unittest
import os
import shutil

from django.test.client import Client
from django.test.utils import override_settings

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from dashboard.sysadmin import create_user
from external_auth.models import ExternalAuthMap
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from xmodule.modulestore.django import modulestore
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.utils.html import escape
from courseware.access import get_access_group_name, has_access
from dashboard.sysadmin import CourseImportLog
import mongoengine

TEST_MONGODB_LOG = {
    'host': 'localhost',
    'user': '',
    'password': '',
    'db': 'test_xlog',
}


class SysadminBaseTestCase(ModuleStoreTestCase):
    """ Base class with common methods used in XML and Mongo tests"""

    def setUp(self):
        super(SysadminBaseTestCase, self).setUp()
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
        try:
            # using XML stor
            course = def_ms.courses.get('{0}/edx4edx_lite'.format(os.path.abspath(settings.DATA_DIR)), None)
        except AttributeError:
            # Using mongo store
            course = def_ms.get_course('MITx/edx4edx/edx4edx')

        # Delete git loaded course
        return self.client.post(reverse('sysadmin'),
                                {'dash_mode': _('Courses'),
                                 'course_id': course.id,
                                 'action': _('Delete course from site'), })


@unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
class TestSysadmin(SysadminBaseTestCase):
    """
    Check that landing page is the status page
    """

    def test_staff_access(self):
        # pylint: disable-msg=E1103

        response = self.client.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])

        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        response = self.client.get(reverse('sysadmin'))
        self.assertEqual('/sysadmin', response.context['next'])

        response = self.client.get(reverse('gitlogs'))
        self.assertEqual(response.status_code, 404)

        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.login(username=self.user.username, password='foo')

        response = self.client.get(reverse('sysadmin'))
        self.assertFalse(hasattr(response.context, 'next'))

        response = self.client.get(reverse('gitlogs'))
        self.assertFalse(hasattr(response.context, 'next'))

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

    def test_git_pull(self):
        """Make sure we can pull"""

        self._setstaff_login()

        response = self._add_edx4edx()
        response = self._add_edx4edx()
        self.assertIn(_("The course {0} already exists in the data directory! "
                        "(reloading anyway)").format('edx4edx_lite'),
                      response.content.decode('utf-8'))
        self._rm_edx4edx()

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


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
@override_settings(MONGODB_LOG=TEST_MONGODB_LOG)
@unittest.skipUnless(settings.MITX_FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'), "ENABLE_SYSADMIN_DASHBOARD not set")
class TestSysAdminMongoCourseImport(SysadminBaseTestCase):
    """
    Check that importing into the mongo module store works
    """

    @classmethod
    def tearDownClass(cls):
        super(TestSysAdminMongoCourseImport, cls).tearDownClass()
        # Delete git repos and mongo objects
        try:
            shutil.rmtree(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass

        try:
            mongoengine.connect(TEST_MONGODB_LOG['db'])
            CourseImportLog.objects.all().delete()
        except mongoengine.connection.ConnectionError:
            pass

    def _setstaff_login(self):
        """ Makes the test user staff and logs them in"""

        self.user.is_staff = True
        self.user.save()

        self.client.login(username=self.user.username, password='foo')

    def test_missing_repo_dir(self):
        """Ensure that we handle a missing repo dir"""

        self._setstaff_login()

        if os.path.isdir(getattr(settings, 'GIT_REPO_DIR')):
            shutil.rmtree(getattr(settings, 'GIT_REPO_DIR'))

        # Create git loaded course
        response = self._add_edx4edx()
        self.assertIn(escape(_("Path {0} doesn't exist, please create it, or configure a "
                               "different path with GIT_REPO_DIR").format(settings.GIT_REPO_DIR)),
                      response.content.decode('UTF-8'))

    def test_mongo_course_add_delete(self):
        """same as TestSysadmin.test_xml_course_add_delete, but use mongo store"""

        self._setstaff_login()
        try:
            os.mkdir(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass

        def_ms = modulestore()
        self.assertIn('mongo', str(def_ms.__class__))

        self._add_edx4edx()
        course = def_ms.get_course('MITx/edx4edx/edx4edx')
        self.assertIsNotNone(course)

        self._rm_edx4edx()
        course = def_ms.get_course('MITx/edx4edx/edx4edx')
        self.assertIsNone(course)

    def test_gitlogs(self):
        """Create a log entry and make sure it exists"""

        self._setstaff_login()
        try:
            os.mkdir(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass

        self._add_edx4edx()
        response = self.client.get(reverse('gitlogs'))

        # Check that our earlier import has a log with a link to details
        self.assertIn('/gitlogs/MITx/edx4edx/edx4edx', response.content)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={'course_id': 'MITx/edx4edx/edx4edx'}))

        self.assertIn('======&gt; IMPORTING course to location', response.content)

        self._rm_edx4edx()

    def test_gitlog_courseteam_access(self):
        """Ensure course team users are allowed to access only their own course"""

        try:
            os.mkdir(getattr(settings, 'GIT_REPO_DIR'))
        except OSError:
            pass

        self._setstaff_login()
        self._add_edx4edx()
        self.user.is_staff = False
        self.user.save()
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        response = self.client.get(reverse('gitlogs'))

        # Make sure our non privileged user doesn't have access to all logs
        self.assertEqual(response.status_code, 404)

        # Add user as staff in course team
        def_ms = modulestore()
        course = def_ms.get_course('MITx/edx4edx/edx4edx')
        
        staff_groupname = get_access_group_name(course, 'staff')
        group, _ = Group.objects.get_or_create(name=staff_groupname)
        self.user.groups.add(group)
        
        self.assertTrue(has_access(self.user, course, 'staff'))
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={'course_id': 'MITx/edx4edx/edx4edx'}))
        print(response.content)
        self.assertIn('======&gt; IMPORTING course to location', response.content)

        self._rm_edx4edx()

    @override_settings(GIT_ADD_COURSE_SCRIPT='')
    def test_no_script_set(self):
        """ Test if settings are right on mongo store import"""

        self._setstaff_login()

        response = self.client.post(reverse('sysadmin'), {
            'dash_mode': _('Courses'),
            'repo_location': 'https://github.com/mitocw/edx4edx_lite.git',
            'action': _('Load new course from github'), })
        self.assertIn(_('Must configure GIT_ADD_COURSE_SCRIPT in settings first!'),
                      response.content)
