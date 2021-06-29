"""
Test for temporary `fix_cert_records` mgmt command.
"""
from django.core.management import call_command

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class FixCertRecordsTest(ModuleStoreTestCase):
    """
    Test cases for `fix_cert_records` mgmt command
    """
    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create()
        self.users = []

    def _create_test_data(self, num_users):
        """
        Utility function to create test data for the tests.
        """
        self.users = [
            UserFactory.create(
                first_name="robot",
                last_name=f"person{i}",
                email=f"robot.person{i}@test.edx.org",
                username=f"robot.person{i}"
            )
            for i in range(num_users)
        ]

        for user in self.users:
            CourseEnrollmentFactory.create(
                is_active=True,
                mode=GeneratedCertificate.MODES.verified,
                course_id=self.course.id,
                user=user
            )
            GeneratedCertificateFactory.create(
                user=user,
                course_id=self.course.id,
                status=CertificateStatuses.unverified,
                mode=GeneratedCertificate.MODES.honor
            )

    def test_happy_path(self):
        self._create_test_data(100)

        call_command("fix_cert_records")

        for user in self.users:
            cert = GeneratedCertificate.objects.get(
                user_id=user.id,
                course_id=self.course.id
            )
            assert cert.mode == GeneratedCertificate.MODES.verified
            assert cert.name == f"{user.first_name} {user.last_name}"

    def test_limit(self):
        self._create_test_data(100)

        call_command("fix_cert_records", "--limit", "50")

        fixed_certs_count = GeneratedCertificate.objects.filter(
            mode=GeneratedCertificate.MODES.verified
        ).count()

        remaining_honor_certs_count = GeneratedCertificate.objects.filter(
            mode=GeneratedCertificate.MODES.honor
        ).count()

        assert fixed_certs_count == 50
        assert remaining_honor_certs_count == 50

        call_command("fix_cert_records", "--limit", "50")

        fixed_certs_count = GeneratedCertificate.objects.filter(
            mode=GeneratedCertificate.MODES.verified
        ).count()

        assert fixed_certs_count == 100
