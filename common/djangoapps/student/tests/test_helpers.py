""" Test Student helpers """

import logging

from django.core.urlresolvers import reverse
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
        unsafe_url = "https://www.amazon.com"
        with LogCapture(LOGGER_NAME, level=logging.ERROR) as logger:
            req = self.request.get(reverse("login") + "?next={url}".format(url=unsafe_url))
            get_next_url_for_login_page(req)
            logger.check(
                (LOGGER_NAME, "ERROR", u"Unsafe redirect parameter detected: u'{url}'".format(url=unsafe_url))
            )

    def test_safe_next(self):
        """ Test safe next parameter """
        req = self.request.get(reverse("login") + "?next={url}".format(url="/dashboard"))
        next_page = get_next_url_for_login_page(req)
        self.assertEqual(next_page, u'/dashboard')
