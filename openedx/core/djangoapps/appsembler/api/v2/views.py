"""Tahoe version 2 API views

Only include view classes here. See the tests/test_permissions.py:get_api_classes()
method.
"""
import beeline
import logging

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import transaction
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.response import Response

from openedx.core.djangoapps.appsembler.api.helpers import normalize_bool_param
from openedx.core.djangoapps.user_authn.views.register import create_account_with_params
from student.helpers import AccountValidationError

from openedx.core.djangoapps.appsembler.api.v1.views import (
    RegistrationViewSet as RegistrationViewSetV1,
    create_password,
    send_password_reset_email
)
from openedx.core.djangoapps.appsembler.api.v2.api import (
    email_exists,
    username_exists
)

# TODO: Just move into v1 directory
from openedx.core.djangoapps.appsembler.api.permissions import (
    TahoeAPIUserThrottle
)


log = logging.getLogger(__name__)


class RegistrationViewSet(RegistrationViewSetV1):
    """
    Allows remote clients to register new users via API

    This API has a rate limit of 60 requets per minutes
    """
    throttle_classes = (TahoeAPIUserThrottle,)
    http_method_names = ['post', 'head']

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):
        return super(RegistrationViewSet, self).dispatch(*args, **kwargs)

    @beeline.traced(name="apis.v2.views.RegistrationViewSet.create")
    def create(self, request):
        """Creates a new user account for the site that calls this view

        Changes between v1 and v2:
        - HttpResponse: 200 on success, {"user_id ": 9} -> {"user_id": 9}

        To use, perform a token authenticated POST to the URL::

            /tahoe/api/v2/registrations/

        Required arguments (JSON data):
            "username"
            "email"
            "name"

        Optional arguments:
            "password"
            "send_activation_email"

        Returns:
            HttpResponse: 200 on success, {"user_id": 9}
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists

        The code here is adapted from the LMS ``appsembler_api`` bulk registration
        code. See the ``appsembler/ginkgo/master`` branch
        """
        # Using .copy() to make the POST data mutable
        # see: https://stackoverflow.com/a/49794425/161278
        data = request.data.copy()
        password_provided = 'password' in data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data['honor_code'] = 'True'
        data['terms_of_service'] = 'True'

        if password_provided:
            try:
                # Default behavior is True - send the email
                data['send_activation_email'] = normalize_bool_param(data.get('send_activation_email', True))
            except ValueError:
                errors = {
                    'user_message': '{0} is not a valid value for "send_activation_email"'.format(
                        data['send_activation_email'])
                }
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            data['password'] = create_password()
            data['send_activation_email'] = False

        email = request.data.get('email')
        username = request.data.get('username')

        # v2: Returns specific error message for duplicate email and/or username
        email_exists_error = email_exists(email=email)
        username_exists_error = username_exists(username=username)
        if email_exists_error and username_exists_error:
            errors = {
                "user_message": "Both email and username already exist",
                "invalid-params": ["email", "username"]
            }
            return Response(errors, status=status.HTTP_409_CONFLICT)
        elif email_exists_error:
            errors = {
                "user_message": "Email already exists",
                "invalid-params": ["email"]
            }
            return Response(errors, status=status.HTTP_409_CONFLICT)
        elif username_exists_error:
            errors = {
                "user_message": "Username already exists",
                "invalid-params": ["username"]
            }
            return Response(errors, status=status.HTTP_409_CONFLICT)

        try:
            user = create_account_with_params(
                request=request,
                params=data,
            )
            if password_provided:
                # if send_activation_email is True, we want to keep the user
                # inactive until the email is properly validated. If the param
                # is False, we activate it.
                user.is_active = not data['send_activation_email']
            else:
                # if the password is not provided, keep the user inactive until
                # the password is set.
                user.is_active = False
            user.save()
            user_id = user.id
            if not password_provided:
                success = send_password_reset_email(request)
                if not success:
                    log.error('Tahoe Reg API: Error sending password reset '
                              'email to user {}'.format(user.username))

        except ValidationError as err:
            log.error('ValidationError. err={}'.format(err))
            # Should only get non-field errors from this function

            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            # TODO: Let's give a clue as to which are the error causing fields
            msg = err
            return Response(dict(user_message=msg), status=status.HTTP_400_BAD_REQUEST)
        except AccountValidationError as err:
            log.error('AccountValidationError. err={}'.format(err))
            # Should only get non-field errors from this function

            # assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            # TODO: Let's give a clue as to which are the error causing fields
            msg = 'Invalid parameters on user creation: {field}'.format(
                field=err.field)
            return Response(dict(user_message=msg), status=status.HTTP_400_BAD_REQUEST)
        return Response({'user_id': user_id}, status=status.HTTP_200_OK)
