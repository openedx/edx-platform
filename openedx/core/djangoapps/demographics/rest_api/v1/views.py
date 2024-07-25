# lint-amnesty, pylint: disable=missing-module-docstring
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.demographics.api.status import show_call_to_action_for_user, show_user_demographics


class DemographicsStatusView(APIView):
    """
    Demographics display status for the User.

    The API will return whether or not to display the Demographics UI based on
    the User's status in the Platform
    """

    permission_classes = (permissions.IsAuthenticated,)

    def _response_context(self, user, user_demographics=None):
        """
        Determine whether the user should be shown demographics collection fields and the demographics call to action.
        """
        if user_demographics:
            show_call_to_action = user_demographics.show_call_to_action
        else:
            show_call_to_action = show_call_to_action_for_user(user)
        return {"display": show_user_demographics(user), "show_call_to_action": show_call_to_action}

    def get(self, request):
        """
        GET /api/user/v1/accounts/demographics/status

        This is a Web API to determine the status of demographics related features
        """
        user = request.user
        return Response(self._response_context(user))
