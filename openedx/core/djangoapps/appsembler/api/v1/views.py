"""Tahoe version 1 API views

"""

import logging
import random
import string

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.conf import settings

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.api import check_account_exists
from student.forms import PasswordResetFormNoActive
from student.views import create_account_with_params

from ..permissions import IsSiteAdminUser


log = logging.getLogger(__name__)

#
# Helper functions
#


def create_password():
    """
    Copied from appsembler_api `CreateUserAccountWithoutPasswordView`
    """
    return ''.join(
        random.choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(32))


def send_password_reset_email(request):
    """Copied/modified from appsembler_api.utils in enterprise Ginkgo
    Copied the template files from enterprise Ginkgo LMS templates
    """
    form = PasswordResetFormNoActive(request.data)
    if form.is_valid():
        form.save(
            use_https=request.is_secure(),
            from_email=configuration_helpers.get_value(
                'email_from_address', settings.DEFAULT_FROM_EMAIL),
            request=request,
            domain_override=request.get_host(),
            subject_template_name='appsembler/emails/set_password_subject.txt',
            email_template_name='appsembler/emails/set_password_email.html')
        return True
    else:
        return False


#
# Mixins for API views
#


class TahoeAuthMixin(object):
    """Provides a common authorization base for the Tahoe multi-site aware API views
    """
    authentication_classes = (
        TokenAuthentication,
    )
    permission_classes = (
        IsAuthenticated,
        IsSiteAdminUser,
    )


class RegistrationViewSet(TahoeAuthMixin, viewsets.ViewSet):

    http_method_names = ['post', 'head']

    def create(self, request):
        """Creates a new user account for the site that calls this view

        To use, perform a token authenticated POST to the URL::

            /tahoe/api/v1/registrations/

        Required arguments (JSON data):
            "username"
            "email"
            "name"

        Optional arguments:
            "password"
            "send_activation_email"

        Returns:
            HttpResponse: 200 on success, {"user_id ": 9}
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists

        The code here is adapted from the LMS ``appsembler_api`` bulk registration
        code. See the ``appsembler/ginkgo/master`` branch
        """
        data = request.data
        password_provided = 'password' in data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data['honor_code'] = "True"
        data['terms_of_service'] = "True"

        if password_provided:
            if 'send_activation_email' in data and data['send_activation_email'] == "False":
                data['send_activation_email'] = False
            else:
                data['send_activation_email'] = True
        else:
            data['password'] = create_password()
            data['send_activation_email'] = False

        email = request.data.get('email')
        username = request.data.get('username')

        # Handle duplicate email/username
        conflicts = check_account_exists(email=email, username=username)
        if conflicts:
            errors = {"user_message": "User already exists"}
            return Response(errors, status=409)

        try:
            user = create_account_with_params(
                request=request,
                params=data,
                send_activation_email_flag=data['send_activation_email'])
            # set the user as active if password is provided
            # meaning we don't have to send a password reset email
            user.is_active = password_provided
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
            errors = {
                "user_message": "Invalid parameters on user creation"
            }
            return Response(errors, status=400)
        return Response({'user_id ': user_id}, status=200)
