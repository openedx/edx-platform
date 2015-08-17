"""
Provide tests for sysadmin dashboard feature in sysadmin.py
"""
import glob
import os
import re
import shutil
import unittest
from util.date_utils import get_time_display, DEFAULT_DATE_TIME_FORMAT
from nose.plugins.attrib import attr

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.timezone import utc as UTC
from django.utils.translation import ugettext as _
import mongoengine
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xmodule.modulestore.tests.django_utils import TEST_DATA_XML_MODULESTORE

from dashboard.models import CourseImportLog
from dashboard.sysadmin import Users
from dashboard.git_import import GitImportError
from datetime import datetime
from external_auth.models import ExternalAuthMap
from student.roles import CourseStaffRole, GlobalStaff
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST


TEST_MONGODB_LOG = {
    'host': MONGO_HOST,
    'port': MONGO_PORT_NUM,
    'user': '',
    'password': '',
    'db': 'test_xlog',
}

FEATURES_WITH_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITH_SSL_AUTH['AUTH_USE_CERTIFICATES'] = True


class SysadminBaseTestCase(ModuleStoreTestCase):
    """
    Base class with common methods used in XML and Mongo tests
    """

    TEST_REPO = 'https://github.com/mitocw/edx4edx_lite.git'
    TEST_BRANCH = 'testing_do_not_delete'
    TEST_BRANCH_COURSE = SlashSeparatedCourseKey('MITx', 'edx4edx_branch', 'edx4edx')

    def setUp(self):
        """Setup test case by adding primary user."""
        super(SysadminBaseTestCase, self).setUp(create_user=False)
        self.user = UserFactory.create(username='test_user',
                                       email='test_user+sysadmin@edx.org',
                                       password='foo')
        self.client = Client()

    def _setstaff_login(self):
        """Makes the test user staff and logs them in"""
        GlobalStaff().add_users(self.user)
        self.client.login(username=self.user.username, password='foo')

    def _add_edx4edx(self, branch=None):
        """Adds the edx4edx sample course"""
        post_dict = {'repo_location': self.TEST_REPO, 'action': 'add_course', }
        if branch:
            post_dict['repo_branch'] = branch
        return self.client.post(reverse('sysadmin_courses'), post_dict)

    def _rm_edx4edx(self):
        """Deletes the sample course from the XML store"""
        def_ms = modulestore()
        course_path = '{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR))
        try:
            # using XML store
            course = def_ms.courses.get(course_path, None)
        except AttributeError:
            # Using mongo store
            course = def_ms.get_course(SlashSeparatedCourseKey('MITx', 'edx4edx', 'edx4edx'))

        # Delete git loaded course
        response = self.client.post(
            reverse('sysadmin_courses'),
            {
                'course_id': course.id.to_deprecated_string(),
                'action': 'del_course',
            }
        )
        self.addCleanup(self._rm_glob, '{0}_deleted_*'.format(course_path))

        return response

    def _rm_glob(self, path):
        """
        Create a shell expansion of passed in parameter and iteratively
        remove them.  Must only expand to directories.
        """
        for path in glob.glob(path):
            shutil.rmtree(path)

    def _mkdir(self, path):
        """
        Create directory and add the cleanup for it.
        """
        os.mkdir(path)
        self.addCleanup(shutil.rmtree, path)


@attr('shard_1')
@unittest.skipUnless(settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
                     "ENABLE_SYSADMIN_DASHBOARD not set")
@override_settings(GIT_IMPORT_WITH_XMLMODULESTORE=True)
class TestSysadmin(SysadminBaseTestCase):
    """
    Test sysadmin dashboard features using XMLModuleStore
    """
    MODULESTORE = TEST_DATA_XML_MODULESTORE

    def test_staff_access(self):
        """Test access controls."""

        test_views = ['sysadmin', 'sysadmin_courses', 'sysadmin_staffing', ]
        for view in test_views:
            response = self.client.get(reverse(view))
            self.assertEqual(response.status_code, 302)

        self.user.is_staff = False
        self.user.save()

        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        for view in test_views:
            response = self.client.get(reverse(view))
            self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('gitlogs'))
        self.assertEqual(response.status_code, 404)

        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.login(username=self.user.username, password='foo')

        for view in test_views:
            response = self.client.get(reverse(view))
            self.assertTrue(response.status_code, 200)

        response = self.client.get(reverse('gitlogs'))
        self.assertTrue(response.status_code, 200)

    def test_user_mod(self):
        """Create and delete a user"""

        self._setstaff_login()

        self.client.login(username=self.user.username, password='foo')

        # Create user tests

        # No uname
        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'create_user',
                                     'student_fullname': 'blah',
                                     'student_password': 'foozor', })
        self.assertIn('Must provide username', response.content.decode('utf-8'))
        # no full name
        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'create_user',
                                     'student_uname': 'test_cuser+sysadmin@edx.org',
                                     'student_password': 'foozor', })
        self.assertIn('Must provide full name', response.content.decode('utf-8'))

        # Test create valid user
        self.client.post(reverse('sysadmin'),
                         {'action': 'create_user',
                          'student_uname': 'test_cuser+sysadmin@edx.org',
                          'student_fullname': 'test cuser',
                          'student_password': 'foozor', })

        self.assertIsNotNone(
            User.objects.get(username='test_cuser+sysadmin@edx.org',
                             email='test_cuser+sysadmin@edx.org'))

        # login as new user to confirm
        self.assertTrue(self.client.login(
            username='test_cuser+sysadmin@edx.org', password='foozor'))

        self.client.logout()
        self.client.login(username=self.user.username, password='foo')

        # Delete user tests

        # Try no username
        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'del_user', })
        self.assertIn('Must provide username', response.content.decode('utf-8'))

        # Try bad usernames
        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'del_user',
                                     'student_uname': 'flabbergast@example.com',
                                     'student_fullname': 'enigma jones', })
        self.assertIn('Cannot find user with email address', response.content.decode('utf-8'))

        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'del_user',
                                     'student_uname': 'flabbergast',
                                     'student_fullname': 'enigma jones', })
        self.assertIn('Cannot find user with username', response.content.decode('utf-8'))

        self.client.post(reverse('sysadmin'),
                         {'action': 'del_user',
                          'student_uname': 'test_cuser+sysadmin@edx.org',
                          'student_fullname': 'test cuser', })

        self.assertEqual(0, len(User.objects.filter(
            username='test_cuser+sysadmin@edx.org',
            email='test_cuser+sysadmin@edx.org')))

        self.assertEqual(1, len(User.objects.all()))

    def test_user_csv(self):
        """Download and validate user CSV"""

        num_test_users = 100
        self._setstaff_login()

        # Stuff full of users to test streaming
        for user_num in xrange(num_test_users):
            Users().create_user('testingman_with_long_name{}'.format(user_num),
                                'test test')

        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'download_users', })

        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual('text/csv', response['Content-Type'])
        self.assertIn('test_user', response.content)
        self.assertTrue(num_test_users + 2, len(response.content.splitlines()))

        # Clean up
        User.objects.filter(
            username__startswith='testingman_with_long_name').delete()

    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH)
    def test_authmap_repair(self):
        """Run authmap check and repair"""

        self._setstaff_login()

        Users().create_user('test0', 'test test')
        # Will raise exception, so no assert needed
        eamap = ExternalAuthMap.objects.get(external_name='test test')
        mitu = User.objects.get(username='test0')

        self.assertTrue(check_password(eamap.internal_password, mitu.password))
        mitu.set_password('not autogenerated')
        mitu.save()
        self.assertFalse(check_password(eamap.internal_password, mitu.password))

        # Create really non user AuthMap
        ExternalAuthMap(external_id='ll',
                        external_domain='ll',
                        external_credentials='{}',
                        external_email='a@b.c',
                        external_name='c',
                        internal_password='').save()

        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'repair_eamap', })

        self.assertIn('{0} test0'.format('Failed in authenticating'),
                      response.content)
        self.assertIn('fixed password', response.content.decode('utf-8'))

        self.assertTrue(self.client.login(username='test0',
                                          password=eamap.internal_password))

        # Check for all OK
        self._setstaff_login()
        response = self.client.post(reverse('sysadmin'),
                                    {'action': 'repair_eamap', })
        self.assertIn('All ok!', response.content.decode('utf-8'))

    def test_xml_course_add_delete(self):
        """add and delete course from xml module store"""

        self._setstaff_login()

        # Try bad git repo
        response = self.client.post(reverse('sysadmin_courses'), {
            'repo_location': 'github.com/mitocw/edx4edx_lite',
            'action': 'add_course', })
        self.assertIn(_("The git repo location should end with '.git', "
                        "and be a valid url"), response.content.decode('utf-8'))

        response = self.client.post(reverse('sysadmin_courses'), {
            'repo_location': 'http://example.com/not_real.git',
            'action': 'add_course', })
        self.assertIn('Unable to clone or pull repository',
                      response.content.decode('utf-8'))
        # Create git loaded course
        response = self._add_edx4edx()

        def_ms = modulestore()

        self.assertEqual('xml', def_ms.get_modulestore_type(None))
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR)), None)
        self.assertIsNotNone(course)

        # Delete a course
        self._rm_edx4edx()
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR)), None)
        self.assertIsNone(course)

        # Load a bad git branch
        response = self._add_edx4edx('asdfasdfasdf')
        self.assertIn(GitImportError.REMOTE_BRANCH_MISSING,
                      response.content.decode('utf-8'))

        # Load a course from a git branch
        self._add_edx4edx(self.TEST_BRANCH)
        course = def_ms.courses.get('{0}/edx4edx_lite'.format(
            os.path.abspath(settings.DATA_DIR)), None)
        self.assertIsNotNone(course)
        self.assertEqual(self.TEST_BRANCH_COURSE, course.id)
        self._rm_edx4edx()

        # Try and delete a non-existent course
        response = self.client.post(reverse('sysadmin_courses'),
                                    {'course_id': 'foobar/foo/blah',
                                     'action': 'del_course', })
        self.assertIn('Error - cannot get course with ID',
                      response.content.decode('utf-8'))

    @override_settings(GIT_IMPORT_WITH_XMLMODULESTORE=False)
    def test_xml_safety_flag(self):
        """Make sure the settings flag to disable xml imports is working"""

        self._setstaff_login()
        response = self._add_edx4edx()
        self.assertIn('GIT_IMPORT_WITH_XMLMODULESTORE', response.content)

        def_ms = modulestore()
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

        def_ms = modulestore()
        course = def_ms.get_course(SlashSeparatedCourseKey('MITx', 'edx4edx', 'edx4edx'))
        CourseStaffRole(course.id).add_users(self.user)

        response = self.client.post(reverse('sysadmin_staffing'),
                                    {'action': 'get_staff_csv', })
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual('text/csv', response['Content-Type'])
        columns = ['course_id', 'role', 'username',
                   'email', 'full_name', ]
        self.assertIn(','.join('"' + c + '"' for c in columns),
                      response.content)

        self._rm_edx4edx()

    def test_enrollment_page(self):
        """
        Adds a course and makes sure that it shows up on the staffing and
        enrollment page
        """

        self._setstaff_login()
        self._add_edx4edx()
        response = self.client.get(reverse('sysadmin_staffing'))
        self.assertIn('edx4edx', response.content)
        self._rm_edx4edx()


@attr('shard_1')
@override_settings(MONGODB_LOG=TEST_MONGODB_LOG)
@unittest.skipUnless(settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
                     "ENABLE_SYSADMIN_DASHBOARD not set")
class TestSysAdminMongoCourseImport(SysadminBaseTestCase):
    """
    Check that importing into the mongo module store works
    """

    @classmethod
    def tearDownClass(cls):
        """Delete mongo log entries after test."""
        super(TestSysAdminMongoCourseImport, cls).tearDownClass()
        try:
            mongoengine.connect(TEST_MONGODB_LOG['db'])
            CourseImportLog.objects.all().delete()
        except mongoengine.connection.ConnectionError:
            pass

    def _setstaff_login(self):
        """
        Makes the test user staff and logs them in
        """

        self.user.is_staff = True
        self.user.save()

        self.client.login(username=self.user.username, password='foo')

    def test_missing_repo_dir(self):
        """
        Ensure that we handle a missing repo dir
        """

        self._setstaff_login()

        if os.path.isdir(getattr(settings, 'GIT_REPO_DIR')):
            shutil.rmtree(getattr(settings, 'GIT_REPO_DIR'))

        # Create git loaded course
        response = self._add_edx4edx()
        self.assertIn(GitImportError.NO_DIR,
                      response.content.decode('UTF-8'))

    def test_mongo_course_add_delete(self):
        """
        This is the same as TestSysadmin.test_xml_course_add_delete,
        but it uses a mongo store
        """

        self._setstaff_login()
        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        def_ms = modulestore()
        self.assertFalse('xml' == def_ms.get_modulestore_type(None))

        self._add_edx4edx()
        course = def_ms.get_course(SlashSeparatedCourseKey('MITx', 'edx4edx', 'edx4edx'))
        self.assertIsNotNone(course)

        self._rm_edx4edx()
        course = def_ms.get_course(SlashSeparatedCourseKey('MITx', 'edx4edx', 'edx4edx'))
        self.assertIsNone(course)

    def test_course_info(self):
        """
        Check to make sure we are getting git info for courses
        """
        # Regex of first 3 columns of course information table row for
        # test course loaded from git. Would not have sha1 if
        # git_info_for_course failed.
        table_re = re.compile(r"""
            <tr>\s+
            <td>edX\sAuthor\sCourse</td>\s+  # expected test git course name
            <td>MITx/edx4edx/edx4edx</td>\s+  # expected test git course_id
            <td>[a-fA-F\d]{40}</td>  # git sha1 hash
        """, re.VERBOSE)

        self._setstaff_login()
        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        # Make sure we don't have any git hashes on the page
        response = self.client.get(reverse('sysadmin_courses'))
        self.assertNotRegexpMatches(response.content, table_re)

        # Now add the course and make sure it does match
        response = self._add_edx4edx()
        self.assertRegexpMatches(response.content, table_re)

    def test_gitlogs(self):
        """
        Create a log entry and make sure it exists
        """

        self._setstaff_login()
        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        self._add_edx4edx()
        response = self.client.get(reverse('gitlogs'))

        # Check that our earlier import has a log with a link to details
        self.assertIn('/gitlogs/MITx/edx4edx/edx4edx', response.content)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'MITx/edx4edx/edx4edx'}))

        self.assertIn('======&gt; IMPORTING course',
                      response.content)

        self._rm_edx4edx()

    def test_gitlog_date(self):
        """
        Make sure the date is timezone-aware and being converted/formatted
        properly.
        """

        tz_names = [
            'America/New_York',  # UTC - 5
            'Asia/Pyongyang',    # UTC + 9
            'Europe/London',     # UTC
            'Canada/Yukon',      # UTC - 8
            'Europe/Moscow',     # UTC + 4
        ]
        tz_format = DEFAULT_DATE_TIME_FORMAT

        self._setstaff_login()
        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        self._add_edx4edx()
        date = CourseImportLog.objects.first().created.replace(tzinfo=UTC)

        for timezone in tz_names:
            with (override_settings(TIME_ZONE=timezone)):
                date_text = get_time_display(date, tz_format, settings.TIME_ZONE)
                response = self.client.get(reverse('gitlogs'))
                self.assertIn(date_text, response.content.decode('UTF-8'))

        self._rm_edx4edx()

    def test_gitlog_bad_course(self):
        """
        Make sure we gracefully handle courses that don't exist.
        """
        self._setstaff_login()
        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'Not/Real/Testing'}))
        self.assertEqual(404, response.status_code)

    def test_gitlog_no_logs(self):
        """
        Make sure the template behaves well when rendered despite there not being any logs.
        (This is for courses imported using methods other than the git_add_course command)
        """

        self._setstaff_login()
        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        self._add_edx4edx()

        # Simulate a lack of git import logs
        import_logs = CourseImportLog.objects.all()
        import_logs.delete()

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'MITx/edx4edx/edx4edx'
            })
        )
        self.assertIn(
            'No git import logs have been recorded for this course.',
            response.content
        )

        self._rm_edx4edx()

    def test_gitlog_pagination_out_of_range_invalid(self):
        """
        Make sure the pagination behaves properly when the requested page is out
        of range.
        """

        self._setstaff_login()

        mongoengine.connect(TEST_MONGODB_LOG['db'])

        for _ in xrange(15):
            CourseImportLog(
                course_id=SlashSeparatedCourseKey("test", "test", "test"),
                location="location",
                import_log="import_log",
                git_log="git_log",
                repo_dir="repo_dir",
                created=datetime.now()
            ).save()

        for page, expected in [(-1, 1), (1, 1), (2, 2), (30, 2), ('abc', 1)]:
            response = self.client.get(
                '{}?page={}'.format(
                    reverse('gitlogs'),
                    page
                )
            )
            self.assertIn(
                'Page {} of 2'.format(expected),
                response.content
            )

        CourseImportLog.objects.delete()

    def test_gitlog_courseteam_access(self):
        """
        Ensure course team users are allowed to access only their own course.
        """

        self._mkdir(getattr(settings, 'GIT_REPO_DIR'))

        self._setstaff_login()
        self._add_edx4edx()
        self.user.is_staff = False
        self.user.save()
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        response = self.client.get(reverse('gitlogs'))
        # Make sure our non privileged user doesn't have access to all logs
        self.assertEqual(response.status_code, 404)
        # Or specific logs
        response = self.client.get(reverse('gitlogs_detail', kwargs={
            'course_id': 'MITx/edx4edx/edx4edx'
        }))
        self.assertEqual(response.status_code, 404)

        # Add user as staff in course team
        def_ms = modulestore()
        course = def_ms.get_course(SlashSeparatedCourseKey('MITx', 'edx4edx', 'edx4edx'))
        CourseStaffRole(course.id).add_users(self.user)

        self.assertTrue(CourseStaffRole(course.id).has_user(self.user))
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'MITx/edx4edx/edx4edx'
            }))
        self.assertIn('======&gt; IMPORTING course',
                      response.content)

        self._rm_edx4edx()
