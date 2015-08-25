"""
Factories related to student verification.
"""

from factory.django import DjangoModelFactory
from verify_student.models import SoftwareSecurePhotoVerification


class SoftwareSecurePhotoVerificationFactory(DjangoModelFactory):
    """
    Factory for SoftwareSecurePhotoVerification
    """
    FACTORY_FOR = SoftwareSecurePhotoVerification

    status = 'approved'
