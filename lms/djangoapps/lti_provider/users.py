"""
LTI user management functionality. This module reconciles the two identities
that an individual has in the campus LMS platform and on edX.
"""

import string
import random
import uuid

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import IntegrityError

from lti_provider.models import LtiUser


def authenticate_lti_user(request, lti_user_id, lti_consumer):
    """
    Determine whether the user specified by the LTI launch has an existing
    account. If not, create a new Django User model and associate it with an
    LtiUser object.

    If the currently logged-in user does not match the user specified by the LTI
    launch, log out the old user and log in the LTI identity.
    """
    try:
        lti_user = LtiUser.objects.get(
            lti_user_id=lti_user_id,
            lti_consumer=lti_consumer
        )
    except LtiUser.DoesNotExist:
        # This is the first time that the user has been here. Create an account.
        lti_user = create_lti_user(lti_user_id, lti_consumer)

    if not (request.user.is_authenticated() and
            request.user == lti_user.edx_user):
        # The user is not authenticated, or is logged in as somebody else.
        # Switch them to the LTI user
        switch_user(request, lti_user)


def create_lti_user(lti_user_id, lti_consumer):
    """
    Generate a new user on the edX platform with a random username and password,
    and associates that account with the LTI identity.
    """
    edx_password = str(uuid.uuid4())

    created = False
    while not created:
        try:
            edx_user_id = generate_random_edx_username()
            edx_user = User.objects.create_user(
                username=edx_user_id,
                password=edx_password,
                email='{}@lti.example.com'.format(edx_user_id)
            )
            edx_user.save()
            created = True
        except IntegrityError:
            # The random edx_user_id wasn't unique. Since 'created' is still
            # False, we will retry with a different random ID.
            pass

    lti_user = LtiUser(
        lti_consumer=lti_consumer,
        lti_user_id=lti_user_id,
        edx_user=edx_user
    )
    lti_user.save()
    return lti_user


def switch_user(request, lti_user):
    """
    Log out the current user, and log in using the edX identity associated with
    the LTI ID.
    """
    # The login function wants to know what backend authenticated the user.
    lti_user.edx_user.backend = 'LTI_Provider'
    login(request, lti_user.edx_user)


def generate_random_edx_username():
    """
    Create a valid random edX user ID. An ID is at most 30 characters long, and
    can contain upper and lowercase letters and numbers.
    :return:
    """
    allowable_chars = string.ascii_letters + string.digits
    username = ''
    for _index in range(30):
        username = username + random.SystemRandom().choice(allowable_chars)
    return username
