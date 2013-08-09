# -*- coding: utf-8 -*- 
"""
Models for Student Identity Verification

Currently the only model is `PhotoVerificationAttempt`, but this is where we
would put any models relating to establishing the real-life identity of a
student over a period of time.
"""
from datetime import datetime
import functools
import logging
import uuid

import pytz
from django.db import models
from django.contrib.auth.models import User

from model_utils.models import StatusModel
from model_utils import Choices

log = logging.getLogger(__name__)


class VerificationException(Exception):
    pass


class IdVerifiedCourses(models.Model):
    """
    A table holding all the courses that are eligible for ID Verification.
    """
    course_id = models.CharField(blank=False, max_length=100)


def status_before_must_be(*valid_start_statuses):
    """
    Decorator with arguments to make sure that an object with a `status`
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
    def decorator_func(fn):
        @functools.wraps(fn)
        def with_status_check(obj, *args, **kwargs):
            if obj.status not in valid_start_statuses:
                exception_msg = (
                    u"Error calling {} {}: status is '{}', must be one of: {}"
                ).format(fn, obj, obj.status, valid_start_statuses)
                raise VerificationException(exception_msg)
            return fn(obj, *args, **kwargs)

        return with_status_check

    return decorator_func


class PhotoVerificationAttempt(StatusModel):
    """
    Each PhotoVerificationAttempt represents a Student's attempt to establish
    their identity by uploading a photo of themselves and a picture ID. An
    attempt actually has a number of fields that need to be filled out at
    different steps of the approval process. While it's useful as a Django Model
    for the querying facilities, **you should only create and edit a 
    `PhotoVerificationAttempt` object through the methods provided**. Do not
    just construct one and start setting fields unless you really know what
    you're doing.

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
    `approved`
        An admin or an external service has confirmed that the user's photo and
        photo ID match up, and that the photo ID's name matches the user's.
    `denied`
        The request has been denied. See `error_msg` for details on why. An
        admin might later override this and change to `approved`, but the 
        student cannot re-open this attempt -- they have to create another
        attempt and submit it instead.

    Because this Model inherits from StatusModel, we can also do things like::
      
        attempt.status == PhotoVerificationAttempt.STATUS.created
        attempt.status == "created"
        pending_requests = PhotoVerificationAttempt.submitted.all()
    """
    ######################## Fields Set During Creation ########################
    # See class docstring for description of status states
    STATUS = Choices('created', 'ready', 'submitted', 'approved', 'denied')
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
        default=uuid.uuid4,
        max_length=255,
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)


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


    ##### Methods listed in the order you'd typically call them
    @classmethod
    def user_is_verified(cls, user_id):
        """Returns whether or not a user has satisfactorily proved their
        identity. Depending on the policy, this can expire after some period of
        time, so a user might have to renew periodically."""
        raise NotImplementedError


    @classmethod
    def active_for_user(cls, user_id):
        """Return all PhotoVerificationAttempts that are still active (i.e. not
        approved or denied).

        Should there only be one active at any given time for a user? Enforced
        at the DB level?
        """
        raise NotImplementedError


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
        if not self.face_image_url:
            raise VerificationException("No face image was uploaded.")
        if not self.photo_id_image_url:
            raise VerificationException("No photo ID image was uploaded.")
        
        # At any point prior to this, they can change their names via their
        # student dashboard. But at this point, we lock the value into the
        # attempt.
        self.name = self.user.profile.name
        self.status = "ready"
        self.save()


    @status_before_must_be("ready", "submit")
    def submit(self, reviewing_service=None):
        if self.status == "submitted":
            return

        if reviewing_service:
            reviewing_service.submit(self)
        self.submitted_at = datetime.now(pytz.UTC)
        self.status = "submitted"
        self.save()


    @status_before_must_be("submitted", "approved", "denied")
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
        
        self.error_msg = ""  # reset, in case this attempt was denied before
        self.error_code = "" # reset, in case this attempt was denied before
        self.reviewing_user = user_id
        self.reviewing_service = service
        self.status = "approved"
        self.save()


    @status_before_must_be("submitted", "approved", "denied")
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
            `reviewed_by_user_id`, `reviewed_by_service`, `error_msg`, `error_code`

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
        self.error_msg = error_msg
        self.error_code = error_code
        self.reviewing_user = reviewing_user
        self.reviewing_service = reviewing_service
        self.status = "denied"
        self.save()


