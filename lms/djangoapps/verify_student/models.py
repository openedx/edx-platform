# -*- coding: utf-8 -*-
"""
Models for Student Identity Verification

This is where we put any models relating to establishing the real-life identity
of a student over a period of time. Right now, the only models are the abstract
`PhotoVerification`, and its one concrete implementation
`SoftwareSecurePhotoVerification`. The hope is to keep as much of the
photo verification process as generic as possible.
"""
import functools
import json
import logging
from datetime import datetime, timedelta
from email.utils import formatdate

import pytz
import requests
import uuid
from lazy import lazy
from opaque_keys.edx.keys import UsageKey

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.dispatch import receiver
from django.db import models, transaction, IntegrityError
from django.utils.translation import ugettext as _, ugettext_lazy

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from simple_history.models import HistoricalRecords
from config_models.models import ConfigurationModel
from course_modes.models import CourseMode
from model_utils.models import StatusModel, TimeStampedModel
from model_utils import Choices
from lms.djangoapps.verify_student.ssencrypt import (
    random_aes_key, encrypt_and_encode,
    generate_signed_message, rsa_encrypt
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule_django.models import CourseKeyField


log = logging.getLogger(__name__)


def generateUUID():  # pylint: disable=invalid-name
    """ Utility function; generates UUIDs """
    return str(uuid.uuid4())


class VerificationException(Exception):
    pass


def status_before_must_be(*valid_start_statuses):
    """
    Helper decorator with arguments to make sure that an object with a `status`
    attribute is in one of a list of acceptable status states before a method
    is called. You could use it in a class definition like:

        @status_before_must_be("submitted", "approved", "denied")
        def refund_user(self, user_id):
            # Do logic here...

    If the object has a status that is not listed when the `refund_user` method
    is invoked, it will throw a `VerificationException`. This is just to avoid
    distracting boilerplate when looking at a Model that needs to go through a
    workflow process.
    """
    def decorator_func(func):
        """
        Decorator function that gets returned
        """
        @functools.wraps(func)
        def with_status_check(obj, *args, **kwargs):
            if obj.status not in valid_start_statuses:
                exception_msg = (
                    u"Error calling {} {}: status is '{}', must be one of: {}"
                ).format(func, obj, obj.status, valid_start_statuses)
                raise VerificationException(exception_msg)
            return func(obj, *args, **kwargs)

        return with_status_check

    return decorator_func


class PhotoVerification(StatusModel):
    """
    Each PhotoVerification represents a Student's attempt to establish
    their identity by uploading a photo of themselves and a picture ID. An
    attempt actually has a number of fields that need to be filled out at
    different steps of the approval process. While it's useful as a Django Model
    for the querying facilities, **you should only edit a `PhotoVerification`
    object through the methods provided**. Initialize them with a user:

    attempt = PhotoVerification(user=user)

    We track this attempt through various states:

    `created`
        Initial creation and state we're in after uploading the images.
    `ready`
        The user has uploaded their images and checked that they can read the
        images. There's a separate state here because it may be the case that we
        don't actually submit this attempt for review until payment is made.
    `submitted`
        Submitted for review. The review may be done by a staff member or an
        external service. The user cannot make changes once in this state.
    `must_retry`
        We submitted this, but there was an error on submission (i.e. we did not
        get a 200 when we POSTed to Software Secure)
    `approved`
        An admin or an external service has confirmed that the user's photo and
        photo ID match up, and that the photo ID's name matches the user's.
    `denied`
        The request has been denied. See `error_msg` for details on why. An
        admin might later override this and change to `approved`, but the
        student cannot re-open this attempt -- they have to create another
        attempt and submit it instead.

    Because this Model inherits from StatusModel, we can also do things like::

        attempt.status == PhotoVerification.STATUS.created
        attempt.status == "created"
        pending_requests = PhotoVerification.submitted.all()
    """
    ######################## Fields Set During Creation ########################
    # See class docstring for description of status states
    STATUS = Choices('created', 'ready', 'submitted', 'must_retry', 'approved', 'denied')
    user = models.ForeignKey(User, db_index=True)

    # They can change their name later on, so we want to copy the value here so
    # we always preserve what it was at the time they requested. We only copy
    # this value during the mark_ready() step. Prior to that, you should be
    # displaying the user's name from their user.profile.name.
    name = models.CharField(blank=True, max_length=255)

    # Where we place the uploaded image files (e.g. S3 URLs)
    face_image_url = models.URLField(blank=True, max_length=255)
    photo_id_image_url = models.URLField(blank=True, max_length=255)

    # Randomly generated UUID so that external services can post back the
    # results of checking a user's photo submission without use exposing actual
    # user IDs or something too easily guessable.
    receipt_id = models.CharField(
        db_index=True,
        default=generateUUID,
        max_length=255,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Indicates whether or not a user wants to see the verification status
    # displayed on their dash.  Right now, only relevant for allowing students
    # to "dismiss" a failed midcourse reverification message
    # TODO: This field is deprecated.
    display = models.BooleanField(db_index=True, default=True)

    ######################## Fields Set When Submitting ########################
    submitted_at = models.DateTimeField(null=True, db_index=True)

    #################### Fields Set During Approval/Denial #####################
    # If the review was done by an internal staff member, mark who it was.
    reviewing_user = models.ForeignKey(
        User,
        db_index=True,
        default=None,
        null=True,
        related_name="photo_verifications_reviewed"
    )

    # Mark the name of the service used to evaluate this attempt (e.g
    # Software Secure).
    reviewing_service = models.CharField(blank=True, max_length=255)

    # If status is "denied", this should contain text explaining why.
    error_msg = models.TextField(blank=True)

    # Non-required field. External services can add any arbitrary codes as time
    # goes on. We don't try to define an exhuastive list -- this is just
    # capturing it so that we can later query for the common problems.
    error_code = models.CharField(blank=True, max_length=50)

    class Meta(object):
        app_label = "verify_student"
        abstract = True
        ordering = ['-created_at']

    ##### Methods listed in the order you'd typically call them
    @classmethod
    def _earliest_allowed_date(cls):
        """
        Returns the earliest allowed date given the settings

        """
        days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        return datetime.now(pytz.UTC) - timedelta(days=days_good_for)

    @classmethod
    def user_is_verified(cls, user, earliest_allowed_date=None):
        """
        Return whether or not a user has satisfactorily proved their identity.
        Depending on the policy, this can expire after some period of time, so
        a user might have to renew periodically.

        This will check for the user's *initial* verification.
        """
        return cls.objects.filter(
            user=user,
            status="approved",
            created_at__gte=(earliest_allowed_date
                             or cls._earliest_allowed_date())
        ).exists()

    @classmethod
    def verification_valid_or_pending(cls, user, earliest_allowed_date=None, queryset=None):
        """
        Check whether the user has a complete verification attempt that is
        or *might* be good. This means that it's approved, been submitted,
        or would have been submitted but had an non-user error when it was
        being submitted.
        It's basically any situation in which the user has signed off on
        the contents of the attempt, and we have not yet received a denial.
        This will check for the user's *initial* verification.

        Arguments:
            user:
            earliest_allowed_date: earliest allowed date given in the
                settings
            queryset: If a queryset is provided, that will be used instead
                of hitting the database.

        Returns:
            queryset: queryset of 'PhotoVerification' sorted by 'created_at' in
            descending order.
        """

        valid_statuses = ['submitted', 'approved', 'must_retry']

        if queryset is None:
            queryset = cls.objects.filter(user=user)

        return queryset.filter(
            status__in=valid_statuses,
            created_at__gte=(
                earliest_allowed_date
                or cls._earliest_allowed_date()
            )
        ).order_by('-created_at')

    @classmethod
    def user_has_valid_or_pending(cls, user, earliest_allowed_date=None, queryset=None):
        """
        Check whether the user has an active or pending verification attempt

        Returns:
            bool: True or False according to existence of valid verifications
        """
        return cls.verification_valid_or_pending(user, earliest_allowed_date, queryset).exists()

    @classmethod
    def active_for_user(cls, user):
        """
        Return the most recent PhotoVerification that is marked ready (i.e. the
        user has said they're set, but we haven't submitted anything yet).

        This checks for the original verification.
        """
        # This should only be one at the most, but just in case we create more
        # by mistake, we'll grab the most recently created one.
        active_attempts = cls.objects.filter(user=user, status='ready').order_by('-created_at')
        if active_attempts:
            return active_attempts[0]
        else:
            return None

    @classmethod
    def user_status(cls, user):
        """
        Returns the status of the user based on their past verification attempts

        If no such verification exists, returns 'none'
        If verification has expired, returns 'expired'
        If the verification has been approved, returns 'approved'
        If the verification process is still ongoing, returns 'pending'
        If the verification has been denied and the user must resubmit photos, returns 'must_reverify'

        This checks initial verifications
        """
        status = 'none'
        error_msg = ''

        if cls.user_is_verified(user):
            status = 'approved'

        elif cls.user_has_valid_or_pending(user):
            # user_has_valid_or_pending does include 'approved', but if we are
            # here, we know that the attempt is still pending
            status = 'pending'

        else:
            # we need to check the most recent attempt to see if we need to ask them to do
            # a retry
            try:
                attempts = cls.objects.filter(user=user).order_by('-updated_at')
                attempt = attempts[0]
            except IndexError:
                # we return 'none'

                return ('none', error_msg)

            if attempt.created_at < cls._earliest_allowed_date():
                return (
                    'expired',
                    _("Your {platform_name} verification has expired.").format(platform_name=settings.PLATFORM_NAME)
                )

            # If someone is denied their original verification attempt, they can try to reverify.
            if attempt.status == 'denied':
                status = 'must_reverify'

            if attempt.error_msg:
                error_msg = attempt.parsed_error_msg()

        return (status, error_msg)

    @classmethod
    def verification_for_datetime(cls, deadline, candidates):
        """Find a verification in a set that applied during a particular datetime.

        A verification is considered "active" during a datetime if:
        1) The verification was created before the datetime, and
        2) The verification is set to expire after the datetime.

        Note that verification status is *not* considered here,
        just the start/expire dates.

        If multiple verifications were active at the deadline,
        returns the most recently created one.

        Arguments:
            deadline (datetime): The datetime at which the verification applied.
                If `None`, then return the most recently created candidate.
            candidates (list of `PhotoVerification`s): Potential verifications to search through.

        Returns:
            PhotoVerification: A photo verification that was active at the deadline.
                If no verification was active, return None.

        """
        if len(candidates) == 0:
            return None

        # If there's no deadline, then return the most recently created verification
        if deadline is None:
            return candidates[0]

        # Otherwise, look for a verification that was in effect at the deadline,
        # preferring recent verifications.
        # If no such verification is found, implicitly return `None`
        for verification in candidates:
            if verification.active_at_datetime(deadline):
                return verification

    @property
    def expiration_datetime(self):
        """Datetime that the verification will expire. """
        days_good_for = settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        return self.created_at + timedelta(days=days_good_for)

    def active_at_datetime(self, deadline):
        """Check whether the verification was active at a particular datetime.

        Arguments:
            deadline (datetime): The date at which the verification was active
                (created before and expired after).

        Returns:
            bool

        """
        return (
            self.created_at < deadline and
            self.expiration_datetime > deadline
        )

    def parsed_error_msg(self):
        """
        Sometimes, the error message we've received needs to be parsed into
        something more human readable

        The default behavior is to return the current error message as is.
        """
        return self.error_msg

    @status_before_must_be("created")
    def upload_face_image(self, img):
        raise NotImplementedError

    @status_before_must_be("created")
    def upload_photo_id_image(self, img):
        raise NotImplementedError

    @status_before_must_be("created")
    def mark_ready(self):
        """
        Mark that the user data in this attempt is correct. In order to
        succeed, the user must have uploaded the necessary images
        (`face_image_url`, `photo_id_image_url`). This method will also copy
        their name from their user profile. Prior to marking it ready, we read
        this value directly from their profile, since they're free to change it.
        This often happens because people put in less formal versions of their
        name on signup, but realize they want something different to go on a
        formal document.

        Valid attempt statuses when calling this method:
            `created`

        Status after method completes: `ready`

        Other fields that will be set by this method:
            `name`

        State Transitions:

        `created` → `ready`
            This is what happens when the user confirms to us that the pictures
            they uploaded are good. Note that we don't actually do a submission
            anywhere yet.
        """
        # At any point prior to this, they can change their names via their
        # student dashboard. But at this point, we lock the value into the
        # attempt.
        self.name = self.user.profile.name
        self.status = "ready"
        self.save()

    @status_before_must_be("must_retry", "submitted", "approved", "denied")
    def approve(self, user_id=None, service=""):
        """
        Approve this attempt. `user_id`

        Valid attempt statuses when calling this method:
            `submitted`, `approved`, `denied`

        Status after method completes: `approved`

        Other fields that will be set by this method:
            `reviewed_by_user_id`, `reviewed_by_service`, `error_msg`

        State Transitions:

        `submitted` → `approved`
            This is the usual flow, whether initiated by a staff user or an
            external validation service.
        `approved` → `approved`
            No-op. First one to approve it wins.
        `denied` → `approved`
            This might happen if a staff member wants to override a decision
            made by an external service or another staff member (say, in
            response to a support request). In this case, the previous values
            of `reviewed_by_user_id` and `reviewed_by_service` will be changed
            to whoever is doing the approving, and `error_msg` will be reset.
            The only record that this record was ever denied would be in our
            logs. This should be a relatively rare occurence.
        """
        # If someone approves an outdated version of this, the first one wins
        if self.status == "approved":
            return

        log.info(u"Verification for user '{user_id}' approved by '{reviewer}'.".format(
            user_id=self.user, reviewer=user_id
        ))
        self.error_msg = ""  # reset, in case this attempt was denied before
        self.error_code = ""  # reset, in case this attempt was denied before
        self.reviewing_user = user_id
        self.reviewing_service = service
        self.status = "approved"
        self.save()

    @status_before_must_be("must_retry", "submitted", "approved", "denied")
    def deny(self,
             error_msg,
             error_code="",
             reviewing_user=None,
             reviewing_service=""):
        """
        Deny this attempt.

        Valid attempt statuses when calling this method:
            `submitted`, `approved`, `denied`

        Status after method completes: `denied`

        Other fields that will be set by this method:
            `reviewed_by_user_id`, `reviewed_by_service`, `error_msg`,
            `error_code`

        State Transitions:

        `submitted` → `denied`
            This is the usual flow, whether initiated by a staff user or an
            external validation service.
        `approved` → `denied`
            This might happen if a staff member wants to override a decision
            made by an external service or another staff member, or just correct
            a mistake made during the approval process. In this case, the
            previous values of `reviewed_by_user_id` and `reviewed_by_service`
            will be changed to whoever is doing the denying. The only record
            that this record was ever approved would be in our logs. This should
            be a relatively rare occurence.
        `denied` → `denied`
            Update the error message and reviewing_user/reviewing_service. Just
            lets you amend the error message in case there were additional
            details to be made.
        """
        log.info(u"Verification for user '{user_id}' denied by '{reviewer}'.".format(
            user_id=self.user, reviewer=reviewing_user
        ))
        self.error_msg = error_msg
        self.error_code = error_code
        self.reviewing_user = reviewing_user
        self.reviewing_service = reviewing_service
        self.status = "denied"
        self.save()

    @status_before_must_be("must_retry", "submitted", "approved", "denied")
    def system_error(self,
                     error_msg,
                     error_code="",
                     reviewing_user=None,
                     reviewing_service=""):
        """
        Mark that this attempt could not be completed because of a system error.
        Status should be moved to `must_retry`. For example, if Software Secure
        reported to us that they couldn't process our submission because they
        couldn't decrypt the image we sent.
        """
        if self.status in ["approved", "denied"]:
            return  # If we were already approved or denied, just leave it.

        self.error_msg = error_msg
        self.error_code = error_code
        self.reviewing_user = reviewing_user
        self.reviewing_service = reviewing_service
        self.status = "must_retry"
        self.save()


class SoftwareSecurePhotoVerification(PhotoVerification):
    """
    Model to verify identity using a service provided by Software Secure. Much
    of the logic is inherited from `PhotoVerification`, but this class
    encrypts the photos.

    Software Secure (http://www.softwaresecure.com/) is a remote proctoring
    service that also does identity verification. A student uses their webcam
    to upload two images: one of their face, one of a photo ID. Due to the
    sensitive nature of the data, the following security precautions are taken:

    1. The snapshot of their face is encrypted using AES-256 in CBC mode. All
       face photos are encypted with the same key, and this key is known to
       both Software Secure and edx-platform.

    2. The snapshot of a user's photo ID is also encrypted using AES-256, but
       the key is randomly generated using pycrypto's Random. Every verification
       attempt has a new key. The AES key is then encrypted using a public key
       provided by Software Secure. We store only the RSA-encryped AES key.
       Since edx-platform does not have Software Secure's private RSA key, it
       means that we can no longer even read photo ID.

    3. The encrypted photos are base64 encoded and stored in an S3 bucket that
       edx-platform does not have read access to.

    Note: this model handles *inital* verifications (which you must perform
    at the time you register for a verified cert).
    """
    # This is a base64.urlsafe_encode(rsa_encrypt(photo_id_aes_key), ss_pub_key)
    # So first we generate a random AES-256 key to encrypt our photo ID with.
    # Then we RSA encrypt it with Software Secure's public key. Then we base64
    # encode that. The result is saved here. Actual expected length is 344.
    photo_id_key = models.TextField(max_length=1024)

    IMAGE_LINK_DURATION = 5 * 60 * 60 * 24  # 5 days in seconds
    copy_id_photo_from = models.ForeignKey("self", null=True, blank=True)

    @classmethod
    def get_initial_verification(cls, user):
        """Get initial verification for a user with the 'photo_id_key'.

        Arguments:
            user(User): user object

        Return:
            SoftwareSecurePhotoVerification (object)
        """
        init_verification = cls.objects.filter(
            user=user,
            status__in=["submitted", "approved"]
        ).exclude(photo_id_key='')

        return init_verification.latest('created_at') if init_verification.exists() else None

    @status_before_must_be("created")
    def upload_face_image(self, img_data):
        """
        Upload an image of the user's face to S3. `img_data` should be a raw
        bytestream of a PNG image. This method will take the data, encrypt it
        using our FACE_IMAGE_AES_KEY, encode it with base64 and save it to S3.

        Yes, encoding it to base64 adds compute and disk usage without much real
        benefit, but that's what the other end of this API is expecting to get.
        """
        # Skip this whole thing if we're running acceptance tests or if we're
        # developing and aren't interested in working on student identity
        # verification functionality. If you do want to work on it, you have to
        # explicitly enable these in your private settings.
        if settings.FEATURES.get('AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'):
            return

        aes_key_str = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["FACE_IMAGE_AES_KEY"]
        aes_key = aes_key_str.decode("hex")

        s3_key = self._generate_s3_key("face")
        s3_key.set_contents_from_string(encrypt_and_encode(img_data, aes_key))

    @status_before_must_be("created")
    def upload_photo_id_image(self, img_data):
        """
        Upload an the user's photo ID image to S3. `img_data` should be a raw
        bytestream of a PNG image. This method will take the data, encrypt it
        using a randomly generated AES key, encode it with base64 and save it to
        S3. The random key is also encrypted using Software Secure's public RSA
        key and stored in our `photo_id_key` field.

        Yes, encoding it to base64 adds compute and disk usage without much real
        benefit, but that's what the other end of this API is expecting to get.
        """
        # Skip this whole thing if we're running acceptance tests or if we're
        # developing and aren't interested in working on student identity
        # verification functionality. If you do want to work on it, you have to
        # explicitly enable these in your private settings.
        if settings.FEATURES.get('AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'):
            # fake photo id key is set only for initial verification
            self.photo_id_key = 'fake-photo-id-key'
            self.save()
            return

        aes_key = random_aes_key()
        rsa_key_str = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["RSA_PUBLIC_KEY"]
        rsa_encrypted_aes_key = rsa_encrypt(aes_key, rsa_key_str)

        # Upload this to S3
        s3_key = self._generate_s3_key("photo_id")
        s3_key.set_contents_from_string(encrypt_and_encode(img_data, aes_key))

        # Update our record fields
        self.photo_id_key = rsa_encrypted_aes_key.encode('base64')
        self.save()

    @status_before_must_be("must_retry", "ready", "submitted")
    def submit(self, copy_id_photo_from=None):
        """
        Submit our verification attempt to Software Secure for validation. This
        will set our status to "submitted" if the post is successful, and
        "must_retry" if the post fails.

        Keyword Arguments:
            copy_id_photo_from (SoftwareSecurePhotoVerification): If provided, re-send the ID photo
                data from this attempt.  This is used for reverification, in which new face photos
                are sent with previously-submitted ID photos.

        """
        try:
            response = self.send_request(copy_id_photo_from=copy_id_photo_from)
            if response.ok:
                self.submitted_at = datetime.now(pytz.UTC)
                self.status = "submitted"
                self.save()
            else:
                self.status = "must_retry"
                self.error_msg = response.text
                self.save()
        except Exception as error:
            log.exception(error)
            self.status = "must_retry"
            self.save()

    def parsed_error_msg(self):
        """
        Parse the error messages we receive from SoftwareSecure

        Error messages are written in the form:

            `[{"photoIdReasons": ["Not provided"]}]`

        Returns a list of error messages
        """
        # Translates the category names and messages into something more human readable
        message_dict = {
            ("photoIdReasons", "Not provided"): _("No photo ID was provided."),
            ("photoIdReasons", "Text not clear"): _("We couldn't read your name from your photo ID image."),
            ("generalReasons", "Name mismatch"): _("The name associated with your account and the name on your ID do not match."),
            ("userPhotoReasons", "Image not clear"): _("The image of your face was not clear."),
            ("userPhotoReasons", "Face out of view"): _("Your face was not visible in your self-photo."),
        }

        try:
            msg_json = json.loads(self.error_msg)
            msg_dict = msg_json[0]

            msg = []
            for category in msg_dict:
                # find the messages associated with this category
                category_msgs = msg_dict[category]
                for category_msg in category_msgs:
                    msg.append(message_dict[(category, category_msg)])
            return u", ".join(msg)
        except (ValueError, KeyError):
            # if we can't parse the message as JSON or the category doesn't
            # match one of our known categories, show a generic error
            log.error('PhotoVerification: Error parsing this error message: %s', self.error_msg)
            return _("There was an error verifying your ID photos.")

    def image_url(self, name, override_receipt_id=None):
        """
        We dynamically generate this, since we want it the expiration clock to
        start when the message is created, not when the record is created.

        Arguments:
            name (str): Name of the image (e.g. "photo_id" or "face")

        Keyword Arguments:
            override_receipt_id (str): If provided, use this receipt ID instead
                of the ID for this attempt.  This is useful for reverification
                where we need to construct a URL to a previously-submitted
                photo ID image.

        Returns:
            string: The expiring URL for the image.

        """
        s3_key = self._generate_s3_key(name, override_receipt_id=override_receipt_id)
        return s3_key.generate_url(self.IMAGE_LINK_DURATION)

    def _generate_s3_key(self, prefix, override_receipt_id=None):
        """
        Generates a key for an s3 bucket location

        Example: face/4dd1add9-6719-42f7-bea0-115c008c4fca
        """
        conn = S3Connection(
            settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["AWS_ACCESS_KEY"],
            settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["AWS_SECRET_KEY"]
        )
        bucket = conn.get_bucket(settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["S3_BUCKET"])

        # Override the receipt ID if one is provided.
        # This allow us to construct S3 keys to images submitted in previous attempts
        # (used for reverification, where we send a new face photo with the same photo ID
        # from a previous attempt).
        receipt_id = self.receipt_id if override_receipt_id is None else override_receipt_id

        key = Key(bucket)
        key.key = "{}/{}".format(prefix, receipt_id)

        return key

    def _encrypted_user_photo_key_str(self):
        """
        Software Secure needs to have both UserPhoto and PhotoID decrypted in
        the same manner. So even though this is going to be the same for every
        request, we're also using RSA encryption to encrypt the AES key for
        faces.
        """
        face_aes_key_str = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["FACE_IMAGE_AES_KEY"]
        face_aes_key = face_aes_key_str.decode("hex")
        rsa_key_str = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["RSA_PUBLIC_KEY"]
        rsa_encrypted_face_aes_key = rsa_encrypt(face_aes_key, rsa_key_str)

        return rsa_encrypted_face_aes_key.encode("base64")

    def create_request(self, copy_id_photo_from=None):
        """
        Construct the HTTP request to the photo verification service.

        Keyword Arguments:
            copy_id_photo_from (SoftwareSecurePhotoVerification): If provided, re-send the ID photo
                data from this attempt.  This is used for reverification, in which new face photos
                are sent with previously-submitted ID photos.

        Returns:
            tuple of (header, body), where both `header` and `body` are dictionaries.

        """
        access_key = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_ACCESS_KEY"]
        secret_key = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_SECRET_KEY"]

        scheme = "https" if settings.HTTPS == "on" else "http"
        callback_url = "{}://{}{}".format(
            scheme, settings.SITE_NAME, reverse('verify_student_results_callback')
        )

        # If we're copying the photo ID image from a previous verification attempt,
        # then we need to send the old image data with the correct image key.
        photo_id_url = (
            self.image_url("photo_id")
            if copy_id_photo_from is None
            else self.image_url("photo_id", override_receipt_id=copy_id_photo_from.receipt_id)
        )

        photo_id_key = (
            self.photo_id_key
            if copy_id_photo_from is None else
            copy_id_photo_from.photo_id_key
        )

        body = {
            "EdX-ID": str(self.receipt_id),
            "ExpectedName": self.name,
            "PhotoID": photo_id_url,
            "PhotoIDKey": photo_id_key,
            "SendResponseTo": callback_url,
            "UserPhoto": self.image_url("face"),
            "UserPhotoKey": self._encrypted_user_photo_key_str(),
        }
        headers = {
            "Content-Type": "application/json",
            "Date": formatdate(timeval=None, localtime=False, usegmt=True)
        }
        _message, _sig, authorization = generate_signed_message(
            "POST", headers, body, access_key, secret_key
        )
        headers['Authorization'] = authorization

        return headers, body

    def request_message_txt(self):
        """
        This is the body of the request we send across. This is never actually
        used in the code, but exists for debugging purposes -- you can call
        `print attempt.request_message_txt()` on the console and get a readable
        rendering of the request that would be sent across, without actually
        sending anything.
        """
        headers, body = self.create_request()

        header_txt = "\n".join(
            "{}: {}".format(h, v) for h, v in sorted(headers.items())
        )
        body_txt = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8')

        return header_txt + "\n\n" + body_txt

    def send_request(self, copy_id_photo_from=None):
        """
        Assembles a submission to Software Secure and sends it via HTTPS.

        Keyword Arguments:
            copy_id_photo_from (SoftwareSecurePhotoVerification): If provided, re-send the ID photo
                data from this attempt.  This is used for reverification, in which new face photos
                are sent with previously-submitted ID photos.

        Returns:
            request.Response

        """
        # If AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING is True, we want to
        # skip posting anything to Software Secure. We actually don't even
        # create the message because that would require encryption and message
        # signing that rely on settings.VERIFY_STUDENT values that aren't set
        # in dev. So we just pretend like we successfully posted
        if settings.FEATURES.get('AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'):
            fake_response = requests.Response()
            fake_response.status_code = 200
            return fake_response

        headers, body = self.create_request(copy_id_photo_from=copy_id_photo_from)
        response = requests.post(
            settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_URL"],
            headers=headers,
            data=json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8'),
            verify=False
        )

        log.info("Sent request to Software Secure for receipt ID %s.", self.receipt_id)
        if copy_id_photo_from is not None:
            log.info(
                (
                    "Software Secure attempt with receipt ID %s used the same photo ID "
                    "data as the receipt with ID %s"
                ),
                self.receipt_id, copy_id_photo_from.receipt_id
            )

        log.debug("Headers:\n{}\n\n".format(headers))
        log.debug("Body:\n{}\n\n".format(body))
        log.debug("Return code: {}".format(response.status_code))
        log.debug("Return message:\n\n{}\n\n".format(response.text))

        return response

    @classmethod
    def verification_status_for_user(cls, user, course_id, user_enrollment_mode):
        """
        Returns the verification status for use in grade report.
        """
        if user_enrollment_mode not in CourseMode.VERIFIED_MODES:
            return 'N/A'

        user_is_verified = cls.user_is_verified(user)

        if not user_is_verified:
            return 'Not ID Verified'
        else:
            return 'ID Verified'


class VerificationDeadline(TimeStampedModel):
    """
    Represent a verification deadline for a particular course.

    The verification deadline is the datetime after which
    users are no longer allowed to submit photos for initial verification
    in a course.

    Note that this is NOT the same as the "upgrade" deadline, after
    which a user is no longer allowed to upgrade to a verified enrollment.

    If no verification deadline record exists for a course,
    then that course does not have a deadline.  This means that users
    can submit photos at any time.
    """
    class Meta(object):
        app_label = "verify_student"

    course_key = CourseKeyField(
        max_length=255,
        db_index=True,
        unique=True,
        help_text=ugettext_lazy(u"The course for which this deadline applies"),
    )

    deadline = models.DateTimeField(
        help_text=ugettext_lazy(
            u"The datetime after which users are no longer allowed "
            u"to submit photos for verification."
        )
    )

    # Maintain a history of changes to deadlines for auditing purposes
    history = HistoricalRecords()

    ALL_DEADLINES_CACHE_KEY = "verify_student.all_verification_deadlines"

    @classmethod
    def set_deadline(cls, course_key, deadline):
        """
        Configure the verification deadline for a course.

        If `deadline` is `None`, then the course will have no verification
        deadline.  In this case, users will be able to verify for the course
        at any time.

        Arguments:
            course_key (CourseKey): Identifier for the course.
            deadline (datetime or None): The verification deadline.

        """
        if deadline is None:
            VerificationDeadline.objects.filter(course_key=course_key).delete()
        else:
            record, created = VerificationDeadline.objects.get_or_create(
                course_key=course_key,
                defaults={"deadline": deadline}
            )

            if not created:
                record.deadline = deadline
                record.save()

    @classmethod
    def deadlines_for_courses(cls, course_keys):
        """
        Retrieve verification deadlines for particular courses.

        Arguments:
            course_keys (list): List of `CourseKey`s.

        Returns:
            dict: Map of course keys to datetimes (verification deadlines)

        """
        all_deadlines = cache.get(cls.ALL_DEADLINES_CACHE_KEY)
        if all_deadlines is None:
            all_deadlines = {
                deadline.course_key: deadline.deadline
                for deadline in VerificationDeadline.objects.all()
            }
            cache.set(cls.ALL_DEADLINES_CACHE_KEY, all_deadlines)

        return {
            course_key: all_deadlines[course_key]
            for course_key in course_keys
            if course_key in all_deadlines
        }

    @classmethod
    def deadline_for_course(cls, course_key):
        """
        Retrieve the verification deadline for a particular course.

        Arguments:
            course_key (CourseKey): The identifier for the course.

        Returns:
            datetime or None

        """
        try:
            deadline = cls.objects.get(course_key=course_key)
            return deadline.deadline
        except cls.DoesNotExist:
            return None


@receiver(models.signals.post_save, sender=VerificationDeadline)
@receiver(models.signals.post_delete, sender=VerificationDeadline)
def invalidate_deadline_caches(sender, **kwargs):  # pylint: disable=unused-argument
    """Invalidate the cached verification deadline information. """
    cache.delete(VerificationDeadline.ALL_DEADLINES_CACHE_KEY)


class VerificationCheckpoint(models.Model):
    """Represents a point at which a user is asked to re-verify his/her
    identity.

    Each checkpoint is uniquely identified by a
    (course_id, checkpoint_location) tuple.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    checkpoint_location = models.CharField(max_length=255)
    photo_verification = models.ManyToManyField(SoftwareSecurePhotoVerification)

    class Meta(object):
        app_label = "verify_student"
        unique_together = ('course_id', 'checkpoint_location')

    def __unicode__(self):
        """
        Unicode representation of the checkpoint.
        """
        return u"{checkpoint} in {course}".format(
            checkpoint=self.checkpoint_name,
            course=self.course_id
        )

    @lazy
    def checkpoint_name(self):
        """Lazy method for getting checkpoint name of reverification block.

        Return location of the checkpoint if no related assessment found in
        database.
        """
        checkpoint_key = UsageKey.from_string(self.checkpoint_location)
        try:
            checkpoint_name = modulestore().get_item(checkpoint_key).related_assessment
        except ItemNotFoundError:
            log.warning(
                u"Verification checkpoint block with location '%s' and course id '%s' "
                u"not found in database.", self.checkpoint_location, unicode(self.course_id)
            )
            checkpoint_name = self.checkpoint_location

        return checkpoint_name

    def add_verification_attempt(self, verification_attempt):
        """Add the verification attempt in M2M relation of photo_verification.

        Arguments:
            verification_attempt(object): SoftwareSecurePhotoVerification object

        Returns:
            None
        """
        self.photo_verification.add(verification_attempt)   # pylint: disable=no-member

    def get_user_latest_status(self, user_id):
        """Get the status of the latest checkpoint attempt of the given user.

        Args:
            user_id(str): Id of user

        Returns:
            VerificationStatus object if found any else None
        """
        try:
            return self.checkpoint_status.filter(user_id=user_id).latest()
        except ObjectDoesNotExist:
            return None

    @classmethod
    def get_or_create_verification_checkpoint(cls, course_id, checkpoint_location):
        """
        Get or create the verification checkpoint for given 'course_id' and
        checkpoint name.

        Arguments:
            course_id (CourseKey): CourseKey
            checkpoint_location (str): Verification checkpoint location

        Raises:
            IntegrityError if create fails due to concurrent create.

        Returns:
            VerificationCheckpoint object if exists otherwise None
        """
        with transaction.atomic():
            checkpoint, __ = cls.objects.get_or_create(course_id=course_id, checkpoint_location=checkpoint_location)
            return checkpoint


class VerificationStatus(models.Model):
    """This model is an append-only table that represents user status changes
    during the verification process.

    A verification status represents a user’s progress through the verification
    process for a particular checkpoint.
    """
    SUBMITTED_STATUS = "submitted"
    APPROVED_STATUS = "approved"
    DENIED_STATUS = "denied"
    ERROR_STATUS = "error"

    VERIFICATION_STATUS_CHOICES = (
        (SUBMITTED_STATUS, SUBMITTED_STATUS),
        (APPROVED_STATUS, APPROVED_STATUS),
        (DENIED_STATUS, DENIED_STATUS),
        (ERROR_STATUS, ERROR_STATUS)
    )

    checkpoint = models.ForeignKey(VerificationCheckpoint, related_name="checkpoint_status")
    user = models.ForeignKey(User)
    status = models.CharField(choices=VERIFICATION_STATUS_CHOICES, db_index=True, max_length=32)
    timestamp = models.DateTimeField(auto_now_add=True)
    response = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    class Meta(object):
        app_label = "verify_student"
        get_latest_by = "timestamp"
        verbose_name = "Verification Status"
        verbose_name_plural = "Verification Statuses"

    @classmethod
    def add_verification_status(cls, checkpoint, user, status):
        """Create new verification status object.

        Arguments:
            checkpoint(VerificationCheckpoint): VerificationCheckpoint object
            user(User): user object
            status(str): Status from VERIFICATION_STATUS_CHOICES

        Returns:
            None
        """
        cls.objects.create(checkpoint=checkpoint, user=user, status=status)

    @classmethod
    def add_status_from_checkpoints(cls, checkpoints, user, status):
        """Create new verification status objects for a user against the given
        checkpoints.

        Arguments:
            checkpoints(list): list of VerificationCheckpoint objects
            user(User): user object
            status(str): Status from VERIFICATION_STATUS_CHOICES

        Returns:
            None
        """
        for checkpoint in checkpoints:
            cls.objects.create(checkpoint=checkpoint, user=user, status=status)

    @classmethod
    def get_user_status_at_checkpoint(cls, user, course_key, location):
        """
        Get the user's latest status at the checkpoint.

        Arguments:
            user (User): The user whose status we are retrieving.
            course_key (CourseKey): The identifier for the course.
            location (UsageKey): The location of the checkpoint in the course.

        Returns:
            unicode or None

        """
        try:
            return cls.objects.filter(
                user=user,
                checkpoint__course_id=course_key,
                checkpoint__checkpoint_location=unicode(location),
            ).latest().status
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_user_attempts(cls, user_id, course_key, checkpoint_location):
        """
        Get re-verification attempts against a user for a given 'checkpoint'
        and 'course_id'.

        Arguments:
            user_id (str): User Id string
            course_key (str): A CourseKey of a course
            checkpoint_location (str): Verification checkpoint location

        Returns:
            Count of re-verification attempts
        """

        return cls.objects.filter(
            user_id=user_id,
            checkpoint__course_id=course_key,
            checkpoint__checkpoint_location=checkpoint_location,
            status=cls.SUBMITTED_STATUS
        ).count()

    @classmethod
    def get_location_id(cls, photo_verification):
        """Get the location ID of reverification XBlock.

        Args:
            photo_verification(object): SoftwareSecurePhotoVerification object

        Return:
            Location Id of XBlock if any else empty string
        """
        try:
            verification_status = cls.objects.filter(checkpoint__photo_verification=photo_verification).latest()
            return verification_status.checkpoint.checkpoint_location
        except cls.DoesNotExist:
            return ""

    @classmethod
    def get_all_checkpoints(cls, user_id, course_key):
        """Return dict of all the checkpoints with their status.
        Args:
            user_id(int): Id of user.
            course_key(unicode): Unicode of course key

        Returns:
            dict: {checkpoint:status}
        """
        all_checks_points = cls.objects.filter(
            user_id=user_id, checkpoint__course_id=course_key
        )
        check_points = {}
        for check in all_checks_points:
            check_points[check.checkpoint.checkpoint_location] = check.status

        return check_points

    @classmethod
    def cache_key_name(cls, user_id, course_key):
        """Return the name of the key to use to cache the current configuration
        Args:
            user_id(int): Id of user.
            course_key(unicode): Unicode of course key

        Returns:
            Unicode cache key
        """
        return u"verification.{}.{}".format(user_id, unicode(course_key))


@receiver(models.signals.post_save, sender=VerificationStatus)
@receiver(models.signals.post_delete, sender=VerificationStatus)
def invalidate_verification_status_cache(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """Invalidate the cache of VerificationStatus model. """

    cache_key = VerificationStatus.cache_key_name(
        instance.user.id,
        unicode(instance.checkpoint.course_id)
    )
    cache.delete(cache_key)


# DEPRECATED: this feature has been permanently enabled.
# Once the application code has been updated in production,
# this table can be safely deleted.
class InCourseReverificationConfiguration(ConfigurationModel):
    """Configure in-course re-verification.

    Enable or disable in-course re-verification feature.
    When this flag is disabled, the "in-course re-verification" feature
    will be disabled.

    When the flag is enabled, the "in-course re-verification" feature
    will be enabled.
    """
    pass


class IcrvStatusEmailsConfiguration(ConfigurationModel):
    """Toggle in-course reverification (ICRV) status emails

    Disabled by default. When disabled, ICRV status emails will not be sent.
    When enabled, ICRV status emails are sent.
    """
    pass


class SkippedReverification(models.Model):
    """Model for tracking skipped Reverification of a user against a specific
    course.

    If a user skipped a Reverification checkpoint for a specific course then in
    future that user cannot see the reverification link.
    """
    user = models.ForeignKey(User)
    course_id = CourseKeyField(max_length=255, db_index=True)
    checkpoint = models.ForeignKey(VerificationCheckpoint, related_name="skipped_checkpoint")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = "verify_student"
        unique_together = (('user', 'course_id'),)

    @classmethod
    @transaction.atomic
    def add_skipped_reverification_attempt(cls, checkpoint, user_id, course_id):
        """Create skipped reverification object.

        Arguments:
            checkpoint(VerificationCheckpoint): VerificationCheckpoint object
            user_id(str): User Id of currently logged in user
            course_id(CourseKey): CourseKey

        Returns:
            None
        """
        cls.objects.create(checkpoint=checkpoint, user_id=user_id, course_id=course_id)

    @classmethod
    def check_user_skipped_reverification_exists(cls, user_id, course_id):
        """Check existence of a user's skipped re-verification attempt for a
        specific course.

        Arguments:
            user_id(str): user id
            course_id(CourseKey): CourseKey

        Returns:
            Boolean
        """
        has_skipped = cls.objects.filter(user_id=user_id, course_id=course_id).exists()
        return has_skipped

    @classmethod
    def cache_key_name(cls, user_id, course_key):
        """Return the name of the key to use to cache the current configuration
        Arguments:
            user(User): user object
            course_key(CourseKey): CourseKey

        Returns:
            string: cache key name
        """
        return u"skipped_reverification.{}.{}".format(user_id, unicode(course_key))


@receiver(models.signals.post_save, sender=SkippedReverification)
@receiver(models.signals.post_delete, sender=SkippedReverification)
def invalidate_skipped_verification_cache(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """Invalidate the cache of skipped verification model. """

    cache_key = SkippedReverification.cache_key_name(
        instance.user.id,
        unicode(instance.course_id)
    )
    cache.delete(cache_key)
