""" Test Student helpers """

import logging

from django.test import TestCase
from django.test.client import RequestFactory
from testfixtures import LogCapture

from student.helpers import get_next_url_for_login_page


LOGGER_NAME = "student.helpers"


class TestLoginHelper(TestCase):
    """Test login helper methods."""
    def setUp(self):
        super(TestLoginHelper, self).setUp()
        self.request = RequestFactory()

    def test_unsafe_next(self):
        """ Test unsafe next parameter """
        with LogCapture(LOGGER_NAME, level=logging.ERROR) as logger:
            req = self.request.get("http://testserver/login?next=http://amazon.com")
            get_next_url_for_login_page(req)
            logger.check(
                (LOGGER_NAME, "ERROR", u"Unsafe redirect parameter detected: u'http://amazon.com'"))

    def test_safe_next(self):
        """ Test safe next parameter """
        req = self.request.get("http://testserver/login?next=/dashboard")
        next_page = get_next_url_for_login_page(req)
        self.assertEqual(next_page, u'/dashboard')
