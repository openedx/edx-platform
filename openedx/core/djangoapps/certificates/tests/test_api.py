

import itertools
from contextlib import contextmanager
from datetime import datetime, timedelta

import ddt
import pytz
import waffle
from django.test import TestCase
from edx_toggles.toggles import WaffleSwitch
from edx_toggles.toggles.testutils import override_waffle_switch

from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.certificates import api
from openedx.core.djangoapps.certificates.config import waffle as certs_waffle
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory


# TODO: Copied from lms.djangoapps.certificates.models,
# to be resolved per https://openedx.atlassian.net/browse/EDUCATOR-1318
class CertificateStatuses(object):
    """
    Enum for certificate statuses
    """
    deleted = 'deleted'
    deleting = 'deleting'
    downloadable = 'downloadable'
    error = 'error'
    generating = 'generating'
    notpassing = 'notpassing'
    restricted = 'restricted'
    unavailable = 'unavailable'
    auditing = 'auditing'
    audit_passing = 'audit_passing'
    audit_notpassing = 'audit_notpassing'
    unverified = 'unverified'
    invalidated = 'invalidated'
    requesting = 'requesting'

    ALL_STATUSES = (
        deleted, deleting, downloadable, error, generating, notpassing, restricted, unavailable, auditing,
        audit_passing, audit_notpassing, unverified, invalidated, requesting
    )


class MockGeneratedCertificate(object):
    """
    We can't import GeneratedCertificate from LMS here, so we roll
    our own minimal Certificate model for testing.
    """
    def __init__(self, user=None, course_id=None, mode=None, status=None):
        self.user = user
        self.course_id = course_id
        self.mode = mode
        self.status = status
        self.created_date = datetime.now(pytz.UTC)
        self.modified_date = datetime.now(pytz.UTC)

    def is_valid(self):
        """
        Return True if certificate is valid else return False.
        """
        return self.status == CertificateStatuses.downloadable


@contextmanager
def configure_waffle_namespace(feature_enabled):
    namespace = certs_waffle.waffle()
    auto_certificate_generation_switch = WaffleSwitch(namespace, certs_waffle.AUTO_CERTIFICATE_GENERATION)
    with override_waffle_switch(auto_certificate_generation_switch, active=feature_enabled):
        yield


@ddt.ddt
class CertificatesApiTestCase(TestCase):
    def setUp(self):
        super(CertificatesApiTestCase, self).setUp()
        self.course = CourseOverviewFactory.create(
            start=datetime(2017, 1, 1, tzinfo=pytz.UTC),
            end=datetime(2017, 1, 31, tzinfo=pytz.UTC),
            certificate_available_date=None
        )
        self.user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode='audit',
        )
        self.certificate = MockGeneratedCertificate(
            user=self.user,
            course_id=self.course.id
        )

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

    @ddt.data(
        (CourseMode.VERIFIED, CertificateStatuses.downloadable, True),
        (CourseMode.VERIFIED, CertificateStatuses.notpassing, False),
        (CourseMode.AUDIT, CertificateStatuses.downloadable, False)
    )
    @ddt.unpack
    def test_is_certificate_valid(self, enrollment_mode, certificate_status, expected_value):
        self.enrollment.mode = enrollment_mode
        self.enrollment.save()

        self.certificate.mode = CourseMode.VERIFIED
        self.certificate.status = certificate_status

        self.assertEqual(expected_value, api.is_certificate_valid(self.certificate))

    @ddt.data(
        (CourseMode.VERIFIED, CertificateStatuses.downloadable, True),
        (CourseMode.VERIFIED, CertificateStatuses.notpassing, False),
        (CourseMode.AUDIT, CertificateStatuses.downloadable, False)
    )
    @ddt.unpack
    def test_available_date(self, enrollment_mode, certificate_status, expected_value):
        self.enrollment.mode = enrollment_mode
        self.enrollment.save()

        self.certificate.mode = CourseMode.VERIFIED
        self.certificate.status = certificate_status

        self.assertEqual(expected_value, api.is_certificate_valid(self.certificate))

    @ddt.data(
        (True, True, False),  # feature enabled and self-paced should return False
        (True, False, True),  # feature enabled and instructor-paced should return True
        (False, True, False),  # feature not enabled and self-paced should return False
        (False, False, False),  # feature not enabled and instructor-paced should return False
    )
    @ddt.unpack
    def test_available_vs_display_date(
            self, feature_enabled, is_self_paced, uses_avail_date
    ):
        self.course.self_paced = is_self_paced
        with configure_waffle_namespace(feature_enabled):

            # With no available_date set, both return modified_date
            self.assertEqual(self.certificate.modified_date, api.available_date_for_certificate(self.course, self.certificate))
            self.assertEqual(self.certificate.modified_date, api.display_date_for_certificate(self.course, self.certificate))

            # With an available date set in the past, both return the available date (if configured)
            self.course.certificate_available_date = datetime(2017, 2, 1, tzinfo=pytz.UTC)
            maybe_avail = self.course.certificate_available_date if uses_avail_date else self.certificate.modified_date
            self.assertEqual(maybe_avail, api.available_date_for_certificate(self.course, self.certificate))
            self.assertEqual(maybe_avail, api.display_date_for_certificate(self.course, self.certificate))

            # With a future available date, they each return a different date
            self.course.certificate_available_date = datetime.max.replace(tzinfo=pytz.UTC)
            maybe_avail = self.course.certificate_available_date if uses_avail_date else self.certificate.modified_date
            self.assertEqual(maybe_avail, api.available_date_for_certificate(self.course, self.certificate))
            self.assertEqual(self.certificate.modified_date, api.display_date_for_certificate(self.course, self.certificate))
