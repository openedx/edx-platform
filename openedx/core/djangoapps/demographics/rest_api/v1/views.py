
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from openedx.core.djangoapps.demographics.api.status import show_user_demographics


class DemographicsStatusView(APIView):
    """
    Demographics display status for the User.

    The API will return whether or not to display the Demographics UI based on
    the User's status in the Platform
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        """
        GET /api/user/v1/accounts/demographics_status

        This is a Web API to determine whether or not we should show Demographics to a learner
        based on their enrollment status.
        """
        user = request.user
        return Response({'display': show_user_demographics(user)})
