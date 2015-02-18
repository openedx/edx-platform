# -*- coding: utf-8 -*-
"""Tests for LinkedIn Add to Profile configuration. """

import ddt
from urllib import urlencode

from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from student.models import LinkedInAddToProfileConfiguration


@ddt.ddt
class LinkedInAddToProfileUrlTests(TestCase):
    """Tests for URL generation of LinkedInAddToProfileConfig. """

    COURSE_KEY = CourseLocator(org="edx", course="DemoX", run="Demo_Course")
    COURSE_NAME = u"Test Course ☃"
    CERT_URL = u"http://s3.edx/cert"

    @ddt.data(
        ('honor', u'edX+Honor+Code+Certificate+for+Test+Course+%E2%98%83'),
        ('verified', u'edX+Verified+Certificate+for+Test+Course+%E2%98%83'),
        ('professional', u'edX+Professional+Certificate+for+Test+Course+%E2%98%83'),
        ('default_mode', u'edX+Certificate+for+Test+Course+%E2%98%83')
    )
    @ddt.unpack
    def test_linked_in_url(self, cert_mode, expected_cert_name):
        config = LinkedInAddToProfileConfiguration(
            company_identifier='0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9',
            enabled=True
        )

        expected_url = (
            'http://www.linkedin.com/profile/add'
            '?_ed=0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9&'
            'pfCertificationName={expected_cert_name}&'
            'pfCertificationUrl=http%3A%2F%2Fs3.edx%2Fcert&'
            'source=o'
        ).format(expected_cert_name=expected_cert_name)

        actual_url = config.add_to_profile_url(
            self.COURSE_KEY,
            self.COURSE_NAME,
            cert_mode,
            self.CERT_URL
        )

        self.assertEqual(actual_url, expected_url)

    def test_linked_in_url_tracking_code(self):
        config = LinkedInAddToProfileConfiguration(
            company_identifier="abcd123",
            trk_partner_name="edx",
            enabled=True
        )

        expected_param = urlencode({
            'trk': u'edx-{course_key}_honor-dashboard'.format(
                course_key=self.COURSE_KEY
            )
        })

        actual_url = config.add_to_profile_url(
            self.COURSE_KEY,
            self.COURSE_NAME,
            'honor',
            self.CERT_URL
        )

        self.assertIn(expected_param, actual_url)
