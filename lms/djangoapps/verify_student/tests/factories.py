"""
Factories related to student verification.
"""
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
