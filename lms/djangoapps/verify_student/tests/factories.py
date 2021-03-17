"""
Factories related to student verification.
"""


from datetime import timedelta  # lint-amnesty, pylint: disable=unused-import

from django.conf import settings  # lint-amnesty, pylint: disable=unused-import
from django.utils.timezone import now  # lint-amnesty, pylint: disable=unused-import
from factory.django import DjangoModelFactory

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSOVerification


class SoftwareSecurePhotoVerificationFactory(DjangoModelFactory):
    """
    Factory for SoftwareSecurePhotoVerification
    """
    class Meta:
        model = SoftwareSecurePhotoVerification

    status = 'approved'


class SSOVerificationFactory(DjangoModelFactory):
    class Meta():
        model = SSOVerification
