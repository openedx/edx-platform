"""
Tests for utility functions in external_auth module
"""
from django.test import TestCase
from openedx.core.djangoapps.external_auth.views import _safe_postlogin_redirect


class ExternalAuthHelperFnTest(TestCase):
    """
    Unit tests for the external_auth.views helper function
    """
    def test__safe_postlogin_redirect(self):
        """
        Tests the _safe_postlogin_redirect function with different values of next
        """
        HOST = 'testserver'                               # pylint: disable=invalid-name
        ONSITE1 = '/dashboard'                            # pylint: disable=invalid-name
        ONSITE2 = '/courses/org/num/name/courseware'      # pylint: disable=invalid-name
        ONSITE3 = 'http://{}/my/custom/url'.format(HOST)  # pylint: disable=invalid-name
        OFFSITE1 = 'http://www.attacker.com'              # pylint: disable=invalid-name

        for redirect_to in [ONSITE1, ONSITE2, ONSITE3]:
            redir = _safe_postlogin_redirect(redirect_to, HOST)
            self.assertEqual(redir.status_code, 302)
            self.assertEqual(redir['location'], redirect_to)

        redir2 = _safe_postlogin_redirect(OFFSITE1, HOST)
        self.assertEqual(redir2.status_code, 302)
        self.assertEqual("/", redir2['location'])
