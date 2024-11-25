"""
Implementation of abstraction layer for other parts of the system to make queries related to ID Verification.
"""

import logging
from datetime import timedelta
from itertools import chain
from urllib.parse import quote

from django.conf import settings
<<<<<<< HEAD
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.utils.translation import gettext as _
=======
from django.utils.timezone import now
from django.utils.translation import gettext as _
from openedx_filters.learning.filters import IDVPageURLRequested
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import User
from lms.djangoapps.verify_student.utils import is_verification_expiring_soon
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

<<<<<<< HEAD
from .models import ManualVerification, SoftwareSecurePhotoVerification, SSOVerification
=======
from .models import ManualVerification, SoftwareSecurePhotoVerification, SSOVerification, VerificationAttempt
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from .utils import most_recent_verification

log = logging.getLogger(__name__)


class XBlockVerificationService:
    """
    Learner verification XBlock service.
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
        return IDVerificationService.user_status(user)

    def reverify_url(self):
        """
        Returns the URL for a user to verify themselves.
        """
        return IDVerificationService.get_verify_location()


class IDVerificationService:
    """
    Learner verification service interface for callers within edx-platform.
    """

    @classmethod
    def user_is_verified(cls, user):
        """
        Return whether or not a user has satisfactorily proved their identity.
        Depending on the policy, this can expire after some period of time, so
        a user might have to renew periodically.
        """
        expiration_datetime = cls.get_expiration_datetime(user, ['approved'])
        if expiration_datetime:
            return expiration_datetime >= now()
        return False

    @classmethod
    def verifications_for_user(cls, user):
        """
        Return a list of all verifications associated with the given user.
        """
        verifications = []
<<<<<<< HEAD
        for verification in chain(SoftwareSecurePhotoVerification.objects.filter(user=user).order_by('-created_at'),
=======
        for verification in chain(VerificationAttempt.objects.filter(user=user).order_by('-created_at'),
                                  SoftwareSecurePhotoVerification.objects.filter(user=user).order_by('-created_at'),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                                  SSOVerification.objects.filter(user=user).order_by('-created_at'),
                                  ManualVerification.objects.filter(user=user).order_by('-created_at')):
            verifications.append(verification)
        return verifications

    @classmethod
    def get_verified_user_ids(cls, users):
        """
        Given a list of users, returns an iterator of user ids that have non-expired verifications of any type.
        """
        filter_kwargs = {
            'user__in': users,
            'status': 'approved',
            'created_at__gt': now() - timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        }
        return chain(
<<<<<<< HEAD
=======
            VerificationAttempt.objects.filter(**{
                'user__in': users,
                'status': 'approved',
                'created_at__gt': now() - timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
            }).values_list('user_id', flat=True),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs).values_list('user_id', flat=True),
            SSOVerification.objects.filter(**filter_kwargs).values_list('user_id', flat=True),
            ManualVerification.objects.filter(**filter_kwargs).values_list('user_id', flat=True)
        )

    @classmethod
    def get_expiration_datetime(cls, user, statuses):
        """
        Check whether the user has a verification with one of the given
        statuses and return the "expiration_datetime" of most recent verification that
        matches one of the given statuses.

        Arguments:
            user (Object): User
            statuses: List of verification statuses (e.g., ['approved'])

        Returns:
            expiration_datetime: expiration_datetime of most recent verification that
            matches one of the given statuses.
        """
        filter_kwargs = {
            'user': user,
            'status__in': statuses,
        }

<<<<<<< HEAD
=======
        id_verifications = VerificationAttempt.objects.filter(**filter_kwargs)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        photo_id_verifications = SoftwareSecurePhotoVerification.objects.filter(**filter_kwargs)
        sso_id_verifications = SSOVerification.objects.filter(**filter_kwargs)
        manual_id_verifications = ManualVerification.objects.filter(**filter_kwargs)

<<<<<<< HEAD
        attempt = most_recent_verification((photo_id_verifications, sso_id_verifications, manual_id_verifications))
=======
        attempt = most_recent_verification(
            (photo_id_verifications, sso_id_verifications, manual_id_verifications, id_verifications)
        )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        return attempt and attempt.expiration_datetime

    @classmethod
    def user_has_valid_or_pending(cls, user):
        """
        Check whether the user has an active or pending verification attempt

        Returns:
            bool: True or False according to existence of valid verifications
        """
        expiration_datetime = cls.get_expiration_datetime(user, ['submitted', 'approved', 'must_retry'])
        if expiration_datetime:
            return expiration_datetime >= now()
        return False

    @classmethod
    def user_status(cls, user):
        """
        Returns the status of the user based on their past verification attempts, and any corresponding error messages.

        If no such verification exists, returns 'none'
        If verification has expired, returns 'expired'
        If the verification has been approved, returns 'approved'
        If the verification process is still ongoing, returns 'pending'
        If the verification has been denied and the user must resubmit photos, returns 'must_reverify'

        This checks most recent verification
        """
        # should_display only refers to displaying the verification attempt status to a user
        # once a verification attempt has been made, otherwise we will display a prompt to complete ID verification.
        user_status = {
            'status': 'none',
            'error': '',
            'should_display': True,
            'status_date': '',
            'verification_expiry': '',
        }

        attempt = None

        verifications = cls.verifications_for_user(user)

        if verifications:
            attempt = verifications[0]
            for verification in verifications:
<<<<<<< HEAD
                if verification.expiration_datetime > now() and verification.status == 'approved':
                    # Always select the LATEST non-expired approved verification if there is such
                    if attempt.status != 'approved' or (
                        attempt.expiration_datetime < verification.expiration_datetime
=======
                # If a verification has no expiration_datetime, it's implied that it never expires, so we should still
                # consider verifications in the approved state that have no expiration date.
                if (
                    not verification.expiration_datetime or
                        verification.expiration_datetime > now()
                ) and verification.status == 'approved':
                    # Always select the LATEST non-expired approved verification if there is such.
                    if (
                        attempt.status != 'approved' or
                        (
                            attempt.expiration_datetime and
                            verification.expiration_datetime and
                            attempt.expiration_datetime < verification.expiration_datetime
                        )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                    ):
                        attempt = verification

        if not attempt:
            return user_status

        user_status['should_display'] = attempt.should_display_status_to_user()

<<<<<<< HEAD
        if attempt.expiration_datetime < now() and attempt.status == 'approved':
=======
        if attempt.expiration_datetime and attempt.expiration_datetime < now() and attempt.status == 'approved':
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            if user_status['should_display']:
                user_status['status'] = 'expired'
                user_status['error'] = _("Your {platform_name} verification has expired.").format(
                    platform_name=configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
                )
            else:
                # If we have a verification attempt that never would have displayed to the user,
                # and that attempt is expired, then we should treat it as if the user had never verified.
                return user_status

        # If someone is denied their original verification attempt, they can try to reverify.
        elif attempt.status == 'denied':
            user_status['status'] = 'must_reverify'
            if hasattr(attempt, 'error_msg') and attempt.error_msg:
                user_status['error'] = attempt.parsed_error_msg()

        elif attempt.status == 'approved':
            user_status['status'] = 'approved'
            expiration_datetime = cls.get_expiration_datetime(user, ['approved'])
            if is_verification_expiring_soon(expiration_datetime):
                user_status['verification_expiry'] = attempt.expiration_datetime.date().strftime("%m/%d/%Y")
            user_status['status_date'] = attempt.status_changed

        elif attempt.status in ['submitted', 'approved', 'must_retry']:
            # user_has_valid_or_pending does include 'approved', but if we are
            # here, we know that the attempt is still pending
            user_status['status'] = 'pending'

        return user_status

    @classmethod
    def verification_status_for_user(cls, user, user_enrollment_mode, user_is_verified=None):
        """
        Returns the verification status for use in grade report.
        """
        if user_enrollment_mode not in CourseMode.VERIFIED_MODES:
            return 'N/A'

        if user_is_verified is None:
            user_is_verified = cls.user_is_verified(user)

        if not user_is_verified:
            return 'Not ID Verified'
        else:
            return 'ID Verified'

    @classmethod
    def get_verify_location(cls, course_id=None):
        """
        Returns a string:
            Returns URL for IDV on Account Microfrontend
        """
        location = f'{settings.ACCOUNT_MICROFRONTEND_URL}/id-verification'
        if course_id:
            location += f'?course_id={quote(str(course_id))}'
<<<<<<< HEAD
        return location

    @classmethod
    def get_verification_details_by_id(cls, attempt_id):
        """
        Returns a verification attempt object by attempt_id
        If the verification object cannot be found, returns None
        """
        verification = None
        verification_models = [
            SoftwareSecurePhotoVerification,
            SSOVerification,
            ManualVerification,
        ]
        for ver_model in verification_models:
            if not verification:
                try:
                    verification = ver_model.objects.get(id=attempt_id)
                except ObjectDoesNotExist:
                    pass
        return verification
=======

        # .. filter_implemented_name: IDVPageURLRequested
        # .. filter_type: org.openedx.learning.idv.page.url.requested.v1
        return IDVPageURLRequested.run_filter(location)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
