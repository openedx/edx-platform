"""
Tests for verified track content views.
"""


import json
import six

from django.http import Http404
from django.test.client import RequestFactory

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory, AdminFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import VerifiedTrackCohortedCourse
from ..views import cohorting_settings


@skip_unless_lms
class CohortingSettingsTestCase(SharedModuleStoreTestCase):
    """
    Tests the `cohort_discussion_topics` view.
    """

    @classmethod
    def setUpClass(cls):
        super(CohortingSettingsTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()

    def test_non_staff(self):
        """
        Verify that we cannot access cohorting_settings if we're a non-staff user.
        """
        request = RequestFactory().get("dummy_url")
        request.user = UserFactory()
        with self.assertRaises(Http404):
            cohorting_settings(request, six.text_type(self.course.id))

    def test_cohorting_settings_enabled(self):
        """
        Verify that cohorting_settings is working for HTTP GET when verified track cohorting is enabled.
        """
        config = VerifiedTrackCohortedCourse.objects.create(
            course_key=six.text_type(self.course.id), enabled=True, verified_cohort_name="Verified Learners"
        )
        config.save()

        expected_response = {
            "enabled": True,
            "verified_cohort_name": "Verified Learners"
        }
        self._verify_cohort_settings_response(expected_response)

    def test_cohorting_settings_disabled(self):
        """
        Verify that cohorting_settings is working for HTTP GET when verified track cohorting is disabled.
        """
        expected_response = {
            "enabled": False
        }
        self._verify_cohort_settings_response(expected_response)

    def _verify_cohort_settings_response(self, expected_response):
        """ Verify that the response was successful and matches the expected JSON payload. """
        request = RequestFactory().get("dummy_url")
        request.user = AdminFactory()
        response = cohorting_settings(request, six.text_type(self.course.id))
        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_response, json.loads(response.content.decode('utf-8')))
