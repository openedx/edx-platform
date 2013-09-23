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
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings

from student.models import CourseEnrollment

from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (studio_store_config,
        ModuleStoreTestCase)
from xmodule.modulestore.xml_importer import import_from_xml

log = logging.getLogger(__name__)

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['OPTIONS']['db'] = 'test_xcontent_%s' % uuid4().hex

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

        base = "http://127.0.0.1:8000"
        self.client = Client()
        self.contentstore = contentstore()

        # A locked the asset
        loc = Location('c4x', 'edX', 'toy', 'asset', 'sample_static.txt' )
        self.loc = loc
        rel_url = StaticContent.get_url_path_from_location(loc)
        self.url = base + rel_url

        # An unlocked asset
        loc2 = Location('c4x', 'edX', 'toy', 'asset', 'another_static.txt' )
        self.loc2 = loc2
        rel_url2 = StaticContent.get_url_path_from_location(loc2)
        self.url2 = base + rel_url2


        import_from_xml(modulestore('direct'), 'common/test/data/', ['toy'],
                static_content_store=self.contentstore, verbose=True)

        self.contentstore.set_attr(self.loc, 'locked', True)


    def tearDown(self):

        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['OPTIONS']['db'])
        _CONTENTSTORE.clear()

    def test_unlocked_asset(self):
        """
        Test that unlocked assets are being served.
        """
        # Logout user
        self.client.logout()

        resp = self.client.get(self.url2)
        self.assertEqual(resp.status_code, 200)


    def test_locked_asset(self):
        """
        Test that locked assets behave appropriately in case:
            (1) User is not logged in
            (2) User is logged in in but not registerd for the course
            (3) User is logged in and registered
        """

        # Case (1)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

        # Case (2)
        #   Create user and login
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'
        user = User.objects.create_user(uname, email, password)
        user.is_active = True
        user.save()
        self.client.login(username=uname, password=password)
        log.debug("User logged in")

        resp = self.client.get(self.url)
        log.debug("Received response %s", resp)
        self.assertEqual(resp.status_code, 403)

        # Case (3)
        #   Enroll student
        course_id = "/".join([self.loc.org, self.loc.course, '2012_Fall'])
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

