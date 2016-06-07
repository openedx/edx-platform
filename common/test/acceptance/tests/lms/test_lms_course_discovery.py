"""
Test course discovery.
"""
import datetime
import json
import uuid

from bok_choy.web_app_test import WebAppTest
from ..helpers import remove_file
from ...pages.common.logout import LogoutPage
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.discovery import CourseDiscoveryPage
from ...fixtures.course import CourseFixture


class CourseDiscoveryTest(WebAppTest):
    """
    Test searching for courses.
    """

    STAFF_USERNAME = "STAFF_TESTER"
    STAFF_EMAIL = "staff101@example.com"
    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self):
        """
        Create course page and courses to find
        """
        # create index file
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)

        self.addCleanup(remove_file, self.TEST_INDEX_FILENAME)

        super(CourseDiscoveryTest, self).setUp()
        self.page = CourseDiscoveryPage(self.browser)

        for i in range(12):
            org = 'test_org'
            number = "{}{}".format(str(i), str(uuid.uuid4().get_hex().upper()[0:6]))
            run = "test_run"
            name = "test course" if i < 10 else "grass is always greener"
            settings = {'enrollment_start': datetime.datetime(1970, 1, 1).isoformat()}
            CourseFixture(org, number, run, name, settings=settings).install()

    def _auto_auth(self, username, email, staff):
        """
        Logout and login with given credentials.
        """
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, username=username, email=email, staff=staff).visit()

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.page.visit()

    def test_search(self):
        """
        Make sure you can search for courses.
        """
        self.page.visit()
        self.assertEqual(len(self.page.result_items), 12)

        self.page.search("grass")
        self.assertEqual(len(self.page.result_items), 2)

        self.page.clear_search()
        self.assertEqual(len(self.page.result_items), 12)
