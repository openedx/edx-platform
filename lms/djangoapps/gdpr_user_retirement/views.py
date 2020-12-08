"""
An API for retiring user accounts.
"""
import logging

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django.models import UserSocialAuth
from student.models import AccountRecovery, Registration, get_retired_email_by_email
from openedx.core.djangolib.oauth2_retirement_utils import retire_dot_oauth2_models
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.user_api.accounts.permissions import CanRetireUser

log = logging.getLogger(__name__)


class GDPRUsersRetirementView(APIView):
    """
    **Use Case**

        Implementation for GDPR User Retirement API. Creates a retirement request
        for one or more users.

    **Example Request**

        POST /v1/accounts/gdpr_retire_users {
            "usernames": "test_user1, test_user2"
        }

        **POST Parameters**

          A POST request can include the following parameter.

          * usernames: Comma separated strings of usernames that should be retired.
    """
    authentication_classes = (JwtAuthentication, )
    permission_classes = (permissions.IsAuthenticated, CanRetireUser)

    def post(self, request, **kwargs):  # pylint: disable=unused-argument
        """
        Initiates the GDPR retirement process for the given users.
        """
        request_usernames = request.data.get('usernames')
        if request_usernames:
            usernames_to_retire = [each_username.strip() for each_username in request_usernames.split(',')]
        else:
            usernames_to_retire = []
        User = get_user_model()
        for username in usernames_to_retire:
            try:
                user_to_retire = User.objects.get(username=username)
                with transaction.atomic():
                    # Add user to retirement queue.
                    UserRetirementStatus.create_retirement(user_to_retire)
                    # Unlink LMS social auth accounts
                    UserSocialAuth.objects.filter(user_id=request.user.id).delete()
                    # Change LMS password & email
                    user_to_retire.email = get_retired_email_by_email(user_to_retire.email)
                    user_to_retire.set_unusable_password()
                    user_to_retire.save()

                    # Remove the activation keys sent by email to the user for account activation.
                    Registration.objects.filter(user=user_to_retire).delete()

                    # Delete OAuth tokens associated with the user.
                    retire_dot_oauth2_models(user_to_retire)
                    AccountRecovery.retire_recovery_email(request.user.id)

            except User.DoesNotExist:
                log.exception('The user "{}" does not exist.'.format(username))
                return Response(
                    u'The user "{}" does not exist.'.format(username), status=status.HTTP_404_NOT_FOUND
                )
            except Exception as exc:  # pylint: disable=broad-except
                log.exception('500 error retiring account {}'.format(exc))
                return Response(str(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)
