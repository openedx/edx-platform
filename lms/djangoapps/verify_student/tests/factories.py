"""
Factories related to student verification.
"""
from __future__ import absolute_import

from datetime import timedelta

from django.conf import settings
from django.utils.timezone import now
from factory.django import DjangoModelFactory

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification


class SoftwareSecurePhotoVerificationFactory(DjangoModelFactory):
    """
    Factory for SoftwareSecurePhotoVerification
    """
    class Meta(object):
        model = SoftwareSecurePhotoVerification

    status = 'approved'
    if hasattr(settings, 'VERIFY_STUDENT'):
        expiry_date = now() + timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
