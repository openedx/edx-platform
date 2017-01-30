""" Test Student helpers """

import logging
import ddt

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from testfixtures import LogCapture

from student.helpers import get_next_url_for_login_page


LOGGER_NAME = "student.helpers"


@ddt.ddt
class TestLoginHelper(TestCase):
    """Test login helper methods."""
    def setUp(self):
        super(TestLoginHelper, self).setUp()
        self.request = RequestFactory()

    @ddt.data(
        ("https://www.amazon.com", "text/html"),
        ("favicon.ico", "image/*"),
        ("https://www.test.com/test.jpg", "image/*"),
        (settings.STATIC_URL + "dummy.png", "image/*"),
    )
    @ddt.unpack
    def test_unsafe_next(self, unsafe_url, http_accept):
        """ Test unsafe next parameter """
        with LogCapture(LOGGER_NAME, level=logging.WARNING) as logger:
            req = self.request.get(reverse("login") + "?next={url}".format(url=unsafe_url))
            req.META["HTTP_ACCEPT"] = http_accept  # pylint: disable=no-member
            get_next_url_for_login_page(req)
            logger.check(
                (LOGGER_NAME, "WARNING",
                 u"Unsafe redirect parameter detected after login page: u'{url}'".format(url=unsafe_url))
            )

    def test_safe_next(self):
        """ Test safe next parameter """
        req = self.request.get(reverse("login") + "?next={url}".format(url="/dashboard"))
        req.META["HTTP_ACCEPT"] = "text/html"  # pylint: disable=no-member
        next_page = get_next_url_for_login_page(req)
        self.assertEqual(next_page, u'/dashboard')
