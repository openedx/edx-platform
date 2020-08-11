
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.demographics.api.status import (
    show_user_demographics, show_call_to_action_for_user,
)
from openedx.core.djangoapps.demographics.models import UserDemographics


class DemographicsStatusView(APIView):
    """
    Demographics display status for the User.

    The API will return whether or not to display the Demographics UI based on
    the User's status in the Platform
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )

    def _response_context(self, user, user_demographics=None):
        if user_demographics:
            show_call_to_action = user_demographics.show_call_to_action
        else:
            show_call_to_action = show_call_to_action_for_user(user)
        return {
            'display': show_user_demographics(user),
            'show_call_to_action': show_call_to_action
        }

    def get(self, request):
        """
        GET /api/user/v1/accounts/demographics/status

        This is a Web API to determine the status of demographics related features
        """
        user = request.user
        return Response(self._response_context(user))

    def patch(self, request):
        """
        PATCH /api/user/v1/accounts/demographics/status

        This is a Web API to update fields that are dependent on user interaction.
        """
        show_call_to_action = request.data.get('show_call_to_action')
        user = request.user
        if not isinstance(show_call_to_action, bool):
            return Response(status.HTTP_400_BAD_REQUEST)
        (user_demographics, _) = UserDemographics.objects.get_or_create(user=user)
        user_demographics.show_call_to_action = show_call_to_action
        user_demographics.save()
        return Response(self._response_context(user, user_demographics))
