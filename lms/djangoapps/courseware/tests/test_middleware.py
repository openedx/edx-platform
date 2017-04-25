"""
Tests for courseware middleware
"""

from django.test.client import RequestFactory
from django.http import Http404
from nose.plugins.attrib import attr

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.courseware.exceptions import Redirect
from lms.djangoapps.courseware.middleware import RedirectMiddleware


@attr(shard=1)
class CoursewareMiddlewareTestCase(SharedModuleStoreTestCase):
    """Tests that courseware middleware is correctly redirected"""

    @classmethod
    def setUpClass(cls):
        super(CoursewareMiddlewareTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(CoursewareMiddlewareTestCase, self).setUp()

    def test_process_404(self):
        """A 404 should not trigger anything"""
        request = RequestFactory().get("dummy_url")
        response = RedirectMiddleware().process_exception(
            request, Http404()
        )
        self.assertIsNone(response)

    def test_redirect_exceptions(self):
        """
        Unit tests for handling of Redirect exceptions.
        """
        request = RequestFactory().get("dummy_url")
        test_url = '/test_url'
        exception = Redirect(test_url)
        response = RedirectMiddleware().process_exception(
            request, exception
        )
        self.assertEqual(response.status_code, 302)
        target_url = response._headers['location'][1]
        self.assertTrue(target_url.endswith(test_url))
