"""
Helpers for the HTTP APIs
"""

from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated


class AuthenticatedAPIView(APIView):
    """
    Returns the number of notifications for the logged in user
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    _allowed_post_parameters = {}

    def validate_post_parameters(self, request):
        """
        Helper to make sure we have valid post parameters names being passed in
        """

        for key, value in request.data.iteritems():

            # check parameter name
            if key not in self._allowed_post_parameters:
                return False

            # check parameter value
            allowed_values = self._allowed_post_parameters[key]
            if value not in allowed_values and allowed_values != '*':
                return False

        return True
