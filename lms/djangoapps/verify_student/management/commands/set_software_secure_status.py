"""
Manually set Software Secure verification status.
"""

import sys

from django.core.management.base import BaseCommand
from verify_student.models import (
    SoftwareSecurePhotoVerification, VerificationCheckpoint, VerificationStatus
)


class Command(BaseCommand):
    """
    Command to trigger the actions that would normally follow Software Secure
    returning with the results of a photo verification.
    """

    args = "<{approved, denied}, SoftwareSecurePhotoVerification id, [reason_for_denial]>"

    def handle(self, *args, **kwargs):  # pylint: disable=unused-argument
        from verify_student.views import _set_user_requirement_status

        status_to_set = args[0]
        receipt_id = args[1]

        try:
            attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=receipt_id)
        except SoftwareSecurePhotoVerification.DoesNotExist:
            self.stderr.write(
                'SoftwareSecurePhotoVerification with id {id} could not be found.\n'.format(id=receipt_id)
            )
            sys.exit(1)

        if status_to_set == 'approved':
            self.stdout.write('Approving verification for {id}.\n'.format(id=receipt_id))
            attempt.approve()
            _set_user_requirement_status(attempt, 'reverification', 'satisfied')

        elif status_to_set == 'denied':
            self.stdout.write('Denying verification for {id}.\n'.format(id=receipt_id))
            if len(args) >= 3:
                reason_for_denial = args[2]
            else:
                reason_for_denial = 'Denied via management command.'
            attempt.deny(reason_for_denial)
            _set_user_requirement_status(attempt, 'reverification', 'failed', reason_for_denial)

        else:
            self.stdout.write('Cannot set id {id} to unrecognized status {status}'.format(
                id=receipt_id, status=status_to_set
            ))
            sys.exit(1)

        checkpoints = VerificationCheckpoint.objects.filter(photo_verification=attempt).all()
        VerificationStatus.add_status_from_checkpoints(
            checkpoints=checkpoints,
            user=attempt.user,
            status=status_to_set
        )
