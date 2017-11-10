"""
Helpers for the HTTP APIs
"""

from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.permissions import IsAuthenticated

from student.admin import User
from django.conf import settings


class CustomTokenSessionAuthentication(BaseAuthentication):
    """
    Custom class to authenticate user via custom Token.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the client sending correct master token & username.
        Otherwise returns `None`.
        """

        username = request.GET.get('username')
        token = request.GET.get("token")

        if not (token or username):
            return None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if not token == settings.NODEBB_MASTER_TOKEN or not user.is_active:
            return None

        return (user, None)


class AuthenticatedAPIView(APIView):
    """
    Returns the number of notifications for the logged in user
    """
    authentication_classes = (SessionAuthentication, CustomTokenSessionAuthentication)
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
