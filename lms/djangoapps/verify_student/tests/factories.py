"""
Factories related to student verification.
"""

from factory.django import DjangoModelFactory
from verify_student.models import SoftwareSecurePhotoVerification


class SoftwareSecurePhotoVerificationFactory(DjangoModelFactory):
    """
    Factory for SoftwareSecurePhotoVerification
    """
    class Meta(object):  # pylint: disable=missing-docstring
        model = SoftwareSecurePhotoVerification

    status = 'approved'
