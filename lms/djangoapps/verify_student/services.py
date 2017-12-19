"""
Implementation of "reverification" service to communicate with Reverification XBlock
"""

import logging

from django.core.urlresolvers import reverse

from student.models import User

from .models import SoftwareSecurePhotoVerification

log = logging.getLogger(__name__)


class VerificationService(object):
    """
    Learner verification XBlock service
    """

    def get_status(self, user_id):
        """
        Returns the user's current photo verification status.

        Args:
            user_id: the user's id

        Returns: one of the following strings
            'none' - no such verification exists
            'expired' - verification has expired
            'approved' - verification has been approved
            'pending' - verification process is still ongoing
            'must_reverify' - verification has been denied and user must resubmit photos
        """
        user = User.objects.get(id=user_id)
        # TODO: provide a photo verification abstraction so that this
        # isn't hard-coded to use Software Secure.
        return SoftwareSecurePhotoVerification.user_status(user)

    def reverify_url(self):
        """
        Returns the URL for a user to verify themselves.
        """
        return reverse('verify_student_reverify')
