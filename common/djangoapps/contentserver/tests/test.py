"""
Tests for StaticContentServer
"""
import copy
import logging
from uuid import uuid4
from path import path
from pymongo import MongoClient

from django.contrib.auth.models import User
from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings

from student.models import CourseEnrollment

from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.tests.django_utils import (studio_store_config,
    ModuleStoreTestCase)
from xmodule.modulestore.xml_importer import import_from_xml

log = logging.getLogger(__name__)

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex

TEST_MODULESTORE = studio_store_config(settings.TEST_ROOT / "data")


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class ContentStoreToyCourseTest(ModuleStoreTestCase):
    """
    Tests that use the toy course.
    """

    def setUp(self):
        """
        Create user and login.
        """

        settings.MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
        settings.MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')

        self.client = Client()
        self.contentstore = contentstore()

        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        import_from_xml(modulestore('direct'), 'common/test/data/', ['toy'],
                static_content_store=self.contentstore, verbose=True)

        # A locked asset
        self.locked_asset = self.course_key.make_asset_key('asset', 'sample_static.txt')
        self.url_locked = self.locked_asset.to_deprecated_string()

        # An unlocked asset
        self.unlocked_asset = self.course_key.make_asset_key('asset', 'another_static.txt')
        self.url_unlocked = self.unlocked_asset.to_deprecated_string()

        self.contentstore.set_attr(self.locked_asset, 'locked', True)

        # Create user
        self.usr = 'testuser'
        self.pwd = 'foo'
        email = 'test+courses@edx.org'
        self.user = User.objects.create_user(self.usr, email, self.pwd)
        self.user.is_active = True
        self.user.save()

        # Create staff user
        self.staff_usr = 'stafftestuser'
        self.staff_pwd = 'foo'
        staff_email = 'stafftest+courses@edx.org'
        self.staff_user = User.objects.create_user(self.staff_usr, staff_email,
                self.staff_pwd)
        self.staff_user.is_active = True
        self.staff_user.is_staff = True
        self.staff_user.save()

    def tearDown(self):

        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'])
        _CONTENTSTORE.clear()

    def test_unlocked_asset(self):
        """
        Test that unlocked assets are being served.
        """
        self.client.logout()
        resp = self.client.get(self.url_unlocked)
        self.assertEqual(resp.status_code, 200) # pylint: disable=E1103

    def test_locked_asset_not_logged_in(self):
        """
        Test that locked assets behave appropriately in case the user is not
        logged in.
        """
        self.client.logout()
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 403) # pylint: disable=E1103

    def test_locked_asset_not_registered(self):
        """
        Test that locked assets behave appropriately in case user is logged in
        in but not registered for the course.
        """
        self.client.login(username=self.usr, password=self.pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 403) # pylint: disable=E1103

    def test_locked_asset_registered(self):
        """
        Test that locked assets behave appropriately in case user is logged in
        and registered for the course.
        """
        CourseEnrollment.enroll(self.user, self.course_key)
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))

        self.client.login(username=self.usr, password=self.pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) # pylint: disable=E1103

    def test_locked_asset_staff(self):
        """
        Test that locked assets behave appropriately in case user is staff.
        """
        self.client.login(username=self.staff_usr, password=self.staff_pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) # pylint: disable=E1103

