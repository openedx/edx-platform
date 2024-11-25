"""
Factories related to student verification.
"""
from factory.django import DjangoModelFactory

<<<<<<< HEAD
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSOVerification
=======
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSOVerification, VerificationAttempt
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


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
<<<<<<< HEAD
=======


class VerificationAttemptFactory(DjangoModelFactory):
    class Meta:
        model = VerificationAttempt
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
