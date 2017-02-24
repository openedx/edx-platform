"""
Mixins for the EnterpriseApiClient.
"""
import json

import httpretty
from django.conf import settings
from django.core.cache import cache


class EnterpriseServiceMockMixin(object):
    """
    Mocks for the Enterprise service responses.
    """

    def setUp(self):
        super(EnterpriseServiceMockMixin, self).setUp()
        cache.clear()

    @staticmethod
    def get_enterprise_url(path):
        """Return a URL to the configured Enterprise API. """
        return '{}{}/'.format(settings.ENTERPRISE_API_URL, path)

    def mock_enterprise_course_enrollment_post_api(  # pylint: disable=invalid-name
            self,
            username='test_user',
            course_id='course-v1:edX+DemoX+Demo_Course',
            consent_granted=True
    ):
        """
        Helper method to register the enterprise course enrollment API POST endpoint.
        """
        api_response = {
            username: username,
            course_id: course_id,
            consent_granted: consent_granted,
        }
        api_response_json = json.dumps(api_response)
        httpretty.register_uri(
            method=httpretty.POST,
            uri=self.get_enterprise_url('enterprise-course-enrollment'),
            body=api_response_json,
            content_type='application/json'
        )

    def mock_enterprise_course_enrollment_post_api_failure(self):  # pylint: disable=invalid-name
        """
        Helper method to register the enterprise course enrollment API endpoint for a failure.
        """
        httpretty.register_uri(
            method=httpretty.POST,
            uri=self.get_enterprise_url('enterprise-course-enrollment'),
            body='{}',
            content_type='application/json',
            status=500
        )
