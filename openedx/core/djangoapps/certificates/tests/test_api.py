from contextlib import contextmanager
import itertools
from unittest import TestCase

import ddt
import waffle

from openedx.core.djangoapps.certificates import api
from openedx.core.djangoapps.certificates.config import waffle as certs_waffle
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


@contextmanager
def configure_waffle_namespace(self_paced_enabled, instructor_paced_enabled):
    namespace = certs_waffle.waffle()

    with namespace.override(certs_waffle.SELF_PACED_ONLY, active=self_paced_enabled):
        with namespace.override(certs_waffle.INSTRUCTOR_PACED_ONLY, active=instructor_paced_enabled):
            yield


@ddt.ddt
class FeatureEnabledTestCase(TestCase):
    def setUp(self):
        super(FeatureEnabledTestCase, self).setUp()
        self.course = CourseOverviewFactory.create()

    def tearDown(self):
        super(FeatureEnabledTestCase, self).tearDown()
        self.course.self_paced = False

    @ddt.data(*itertools.product((True, False), (True, False)))
    @ddt.unpack
    def test_auto_certificate_generation_enabled(self, self_paced_enabled, instructor_paced_enabled):
        expected_value = self_paced_enabled or instructor_paced_enabled
        with configure_waffle_namespace(self_paced_enabled, instructor_paced_enabled):
            self.assertEqual(expected_value, api.auto_certificate_generation_enabled())

    @ddt.data(
        (False, False, True, False),  # feature not enabled should return False
        (False, True, True, False),  # self-paced feature enabled and self-paced course should return False
        (True, False, True, True),  # self-paced feature enabled and self-paced course should return True
        (True, False, False, False),  # instructor-paced feature enabled and self-paced course should return False
        (False, True, False, True)  # instructor-paced feature enabled and instructor-paced course should return True
    )
    @ddt.unpack
    def test_auto_certificate_generation_enabled_for_course(
            self, self_paced_enabled, instructor_paced_enabled, is_self_paced, expected_value
    ):
        self.course.self_paced = is_self_paced
        with configure_waffle_namespace(self_paced_enabled, instructor_paced_enabled):
            self.assertEqual(expected_value, api.auto_certificate_generation_enabled_for_course(self.course))

    @ddt.data(
        (True, False, True, False),  # feature enabled and self-paced should return False
        (False, True, False, True),  # feature enabled and instructor-paced should return True
        (False, False, True, False),  # feature not enabled and self-paced should return False
        (False, False, False, False),  # feature not enabled and instructor-paced should return False
    )
    @ddt.unpack
    def test_can_show_certificate_available_date_field(
            self, self_paced_enabled, instructor_paced_enabled, is_self_paced, expected_value
    ):
        self.course.self_paced = is_self_paced
        with configure_waffle_namespace(self_paced_enabled, instructor_paced_enabled):
            self.assertEqual(expected_value, api.can_show_certificate_available_date_field(self.course))
