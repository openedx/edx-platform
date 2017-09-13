from contextlib import contextmanager
import itertools
from unittest import TestCase

import ddt
import waffle

from openedx.core.djangoapps.certificates import api
from openedx.core.djangoapps.certificates.config import waffle as certs_waffle
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


@contextmanager
def configure_waffle_namespace(feature_enabled):
    namespace = certs_waffle.waffle()

    with namespace.override(certs_waffle.AUTO_CERTIFICATE_GENERATION, active=feature_enabled):
            yield


@ddt.ddt
class FeatureEnabledTestCase(TestCase):
    def setUp(self):
        super(FeatureEnabledTestCase, self).setUp()
        self.course = CourseOverviewFactory.create()

    def tearDown(self):
        super(FeatureEnabledTestCase, self).tearDown()
        self.course.self_paced = False

    @ddt.data(True, False)
    def test_auto_certificate_generation_enabled(self, feature_enabled):
        with configure_waffle_namespace(feature_enabled):
            self.assertEqual(feature_enabled, api.auto_certificate_generation_enabled())

    @ddt.data(
        (True, True, False),  # feature enabled and self-paced should return False
        (True, False, True),  # feature enabled and instructor-paced should return True
        (False, True, False),  # feature not enabled and self-paced should return False
        (False, False, False),  # feature not enabled and instructor-paced should return False
    )
    @ddt.unpack
    def test_can_show_certificate_available_date_field(
            self, feature_enabled, is_self_paced, expected_value
    ):
        self.course.self_paced = is_self_paced
        with configure_waffle_namespace(feature_enabled):
            self.assertEqual(expected_value, api.can_show_certificate_available_date_field(self.course))
