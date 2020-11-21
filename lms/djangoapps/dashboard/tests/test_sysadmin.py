"""
Provide tests for sysadmin dashboard feature in sysadmin.py
"""


import glob
import os
import re
import shutil
import unittest
from datetime import datetime
from uuid import uuid4

import mongoengine
from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings
from django.urls import reverse
from opaque_keys.edx.locator import CourseLocator
from pytz import UTC
from six import text_type
from six.moves import range

from lms.djangoapps.dashboard.git_import import GitImportErrorNoDir
from lms.djangoapps.dashboard.models import CourseImportLog
from openedx.core.djangolib.markup import Text
from common.djangoapps.student.roles import CourseStaffRole, GlobalStaff
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.date_utils import DEFAULT_DATE_TIME_FORMAT, get_time_display
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.mongo_connection import MONGO_HOST, MONGO_PORT_NUM

TEST_MONGODB_LOG = {
    'host': MONGO_HOST,
    'port': MONGO_PORT_NUM,
    'user': '',
    'password': '',
    'db': 'test_xlog',
}


class SysadminBaseTestCase(SharedModuleStoreTestCase):
    """
    Base class with common methods used in XML and Mongo tests
    """

    TEST_REPO = 'https://github.com/edx/edx4edx_lite.git'
    TEST_BRANCH = 'testing_do_not_delete'
    TEST_BRANCH_COURSE = CourseLocator.from_string('course-v1:MITx+edx4edx_branch+edx4edx')
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """Setup test case by adding primary user."""
        super(SysadminBaseTestCase, self).setUp()
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
            course = def_ms.get_course(CourseLocator('MITx', 'edx4edx', 'edx4edx'))

        # Delete git loaded course
        response = self.client.post(
            reverse('sysadmin_courses'),
            {
                'course_id': text_type(course.id),
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


@override_settings(
    MONGODB_LOG=TEST_MONGODB_LOG,
    GIT_REPO_DIR=settings.TEST_ROOT / "course_repos_{}".format(uuid4().hex)
)
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
        except mongoengine.connection.ConnectionFailure:
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

        if os.path.isdir(settings.GIT_REPO_DIR):
            shutil.rmtree(settings.GIT_REPO_DIR)

        # Create git loaded course
        response = self._add_edx4edx()
        self.assertContains(response, Text(text_type(GitImportErrorNoDir(settings.GIT_REPO_DIR))))

    def test_mongo_course_add_delete(self):
        """
        This is the same as TestSysadmin.test_xml_course_add_delete,
        but it uses a mongo store
        """

        self._setstaff_login()
        self._mkdir(settings.GIT_REPO_DIR)

        def_ms = modulestore()
        self.assertNotEqual('xml', def_ms.get_modulestore_type(None))

        self._add_edx4edx()
        course = def_ms.get_course(CourseLocator('MITx', 'edx4edx', 'edx4edx'))
        self.assertIsNotNone(course)

        self._rm_edx4edx()
        course = def_ms.get_course(CourseLocator('MITx', 'edx4edx', 'edx4edx'))
        self.assertIsNone(course)

    def test_course_info(self):
        """
        Check to make sure we are getting git info for courses
        """
        # Regex of first 3 columns of course information table row for
        # test course loaded from git. Would not have sha1 if
        # git_info_for_course failed.
        table_re = re.compile(u"""
            <tr>\\s+
            <td>edX\\sAuthor\\sCourse</td>\\s+  # expected test git course name
            <td>course-v1:MITx\\+edx4edx\\+edx4edx</td>\\s+  # expected test git course_id
            <td>[a-fA-F\\d]{40}</td>  # git sha1 hash
        """, re.VERBOSE)
        self._setstaff_login()
        self._mkdir(settings.GIT_REPO_DIR)

        # Make sure we don't have any git hashes on the page
        response = self.client.get(reverse('sysadmin_courses'))
        self.assertNotRegex(response.content.decode('utf-8'), table_re)

        # Now add the course and make sure it does match
        response = self._add_edx4edx()
        self.assertRegex(response.content.decode('utf-8'), table_re)

    def test_gitlogs(self):
        """
        Create a log entry and make sure it exists
        """

        self._setstaff_login()
        self._mkdir(settings.GIT_REPO_DIR)

        self._add_edx4edx()
        response = self.client.get(reverse('gitlogs'))

        # Check that our earlier import has a log with a link to details
        self.assertContains(response, '/gitlogs/course-v1:MITx+edx4edx+edx4edx')

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'course-v1:MITx+edx4edx+edx4edx'}))

        self.assertContains(response, '======&gt; IMPORTING course')

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
        self._mkdir(settings.GIT_REPO_DIR)

        self._add_edx4edx()
        date = CourseImportLog.objects.first().created.replace(tzinfo=UTC)

        for timezone in tz_names:
            with (override_settings(TIME_ZONE=timezone)):
                date_text = get_time_display(date, tz_format, settings.TIME_ZONE)
                response = self.client.get(reverse('gitlogs'))
                self.assertContains(response, date_text)

        self._rm_edx4edx()

    def test_gitlog_bad_course(self):
        """
        Make sure we gracefully handle courses that don't exist.
        """
        self._setstaff_login()
        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'Not/Real/Testing'}))
        self.assertContains(
            response,
            'No git import logs have been recorded for this course.',
        )

    def test_gitlog_no_logs(self):
        """
        Make sure the template behaves well when rendered despite there not being any logs.
        (This is for courses imported using methods other than the git_add_course command)
        """

        self._setstaff_login()
        self._mkdir(settings.GIT_REPO_DIR)

        self._add_edx4edx()

        # Simulate a lack of git import logs
        import_logs = CourseImportLog.objects.all()
        import_logs.delete()

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'course-v1:MITx+edx4edx+edx4edx'
            })
        )
        self.assertContains(response, 'No git import logs have been recorded for this course.')

        self._rm_edx4edx()

    def test_gitlog_pagination_out_of_range_invalid(self):
        """
        Make sure the pagination behaves properly when the requested page is out
        of range.
        """

        self._setstaff_login()

        mongoengine.connect(TEST_MONGODB_LOG['db'])

        for _ in range(15):
            CourseImportLog(
                course_id=CourseLocator.from_string("test/test/test"),
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
            self.assertContains(response, u'Page {} of 2'.format(expected))

        CourseImportLog.objects.delete()

    def test_gitlog_courseteam_access(self):
        """
        Ensure course team users are allowed to access only their own course.
        """

        self._mkdir(settings.GIT_REPO_DIR)

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
            'course_id': 'course-v1:MITx+edx4edx+edx4edx'
        }))
        self.assertEqual(response.status_code, 404)

        # Add user as staff in course team
        def_ms = modulestore()
        course = def_ms.get_course(CourseLocator('MITx', 'edx4edx', 'edx4edx'))
        CourseStaffRole(course.id).add_users(self.user)

        self.assertTrue(CourseStaffRole(course.id).has_user(self.user))
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)

        response = self.client.get(
            reverse('gitlogs_detail', kwargs={
                'course_id': 'course-v1:MITx+edx4edx+edx4edx'
            }))
        self.assertContains(response, '======&gt; IMPORTING course')

        self._rm_edx4edx()
