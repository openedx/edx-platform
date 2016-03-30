"""
Tests for courseware middleware
"""

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.http import Http404
from mock import patch
from nose.plugins.attrib import attr

import courseware.courses as courses
from courseware.middleware import RedirectUnenrolledMiddleware
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr('shard_1')
class CoursewareMiddlewareTestCase(SharedModuleStoreTestCase):
    """Tests that courseware middleware is correctly redirected"""

    @classmethod
    def setUpClass(cls):
        super(CoursewareMiddlewareTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(CoursewareMiddlewareTestCase, self).setUp()

    def check_user_not_enrolled_redirect(self):
        """A UserNotEnrolled exception should trigger a redirect"""
        request = RequestFactory().get("dummy_url")
        response = RedirectUnenrolledMiddleware().process_exception(
            request, courses.UserNotEnrolled(self.course.id)
        )
        self.assertEqual(response.status_code, 302)
        # make sure we redirect to the course about page
        expected_url = reverse(
            "about_course", args=[self.course.id.to_deprecated_string()]
        )

        target_url = response._headers['location'][1]
        self.assertTrue(target_url.endswith(expected_url))

    def test_user_not_enrolled_redirect(self):
        self.check_user_not_enrolled_redirect()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_MKTG_SITE": True})
    def test_user_not_enrolled_redirect_mktg(self):
        self.check_user_not_enrolled_redirect()

    def test_process_404(self):
        """A 404 should not trigger anything"""
        request = RequestFactory().get("dummy_url")
        response = RedirectUnenrolledMiddleware().process_exception(
            request, Http404()
        )
        self.assertIsNone(response)
