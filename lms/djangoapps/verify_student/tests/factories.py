"""
Factories related to student verification.
"""

from factory.django import DjangoModelFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification


class SoftwareSecurePhotoVerificationFactory(DjangoModelFactory):
    """
    Factory for SoftwareSecurePhotoVerification
    """
    class Meta(object):
        model = SoftwareSecurePhotoVerification

    status = 'approved'
