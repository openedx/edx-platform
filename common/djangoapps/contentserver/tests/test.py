"""
Tests for StaticContentServer
"""
import copy
import logging
from uuid import uuid4

from django.conf import settings
from django.test.client import Client
from django.test.utils import override_settings

from student.models import CourseEnrollment

from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_from_xml

log = logging.getLogger(__name__)

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ContentStoreToyCourseTest(ModuleStoreTestCase):
    """
    Tests that use the toy course.
    """

    def setUp(self):
        """
        Create user and login.
        """
        self.staff_pwd = super(ContentStoreToyCourseTest, self).setUp()
        self.staff_usr = self.user
        self.non_staff_usr, self.non_staff_pwd = self.create_non_staff_user()

        self.client = Client()
        self.contentstore = contentstore()

        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        import_from_xml(modulestore(), self.user.id, 'common/test/data/', ['toy'],
                static_content_store=self.contentstore, verbose=True)

        # A locked asset
        self.locked_asset = self.course_key.make_asset_key('asset', 'sample_static.txt')
        self.url_locked = self.locked_asset.to_deprecated_string()

        # An unlocked asset
        self.unlocked_asset = self.course_key.make_asset_key('asset', 'another_static.txt')
        self.url_unlocked = self.unlocked_asset.to_deprecated_string()

        self.contentstore.set_attr(self.locked_asset, 'locked', True)

    def tearDown(self):

        contentstore().drop_database()
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
        self.client.login(username=self.non_staff_usr, password=self.non_staff_pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 403) # pylint: disable=E1103

    def test_locked_asset_registered(self):
        """
        Test that locked assets behave appropriately in case user is logged in
        and registered for the course.
        """
        CourseEnrollment.enroll(self.non_staff_usr, self.course_key)
        self.assertTrue(CourseEnrollment.is_enrolled(self.non_staff_usr, self.course_key))

        self.client.login(username=self.non_staff_usr, password=self.non_staff_pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) # pylint: disable=E1103

    def test_locked_asset_staff(self):
        """
        Test that locked assets behave appropriately in case user is staff.
        """
        self.client.login(username=self.staff_usr, password=self.staff_pwd)
        resp = self.client.get(self.url_locked)
        self.assertEqual(resp.status_code, 200) # pylint: disable=E1103

