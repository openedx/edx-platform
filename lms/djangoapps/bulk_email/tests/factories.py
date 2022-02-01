"""
Provides factories for BulkEmail models.
"""

from factory.django import DjangoModelFactory

from lms.djangoapps.bulk_email.models import SEND_TO_LEARNERS, Target


class TargetFactory(DjangoModelFactory):
    class Meta:
        model = Target

    target_type = SEND_TO_LEARNERS
