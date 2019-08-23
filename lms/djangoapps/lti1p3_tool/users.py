from __future__ import absolute_import

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from lti_provider.users import LtiBackend, UserService
from .models import LtiUser


class Lti1p3UserService(UserService):

    def get_lti_user(self, lti_jwt_sub, lti_tool):
        try:
            lti_user = LtiUser.objects.get(
                lti_jwt_sub=lti_jwt_sub,
                lti_tool=lti_tool
            )
        except LtiUser.DoesNotExist:
            # This is the first time that the user has been here. Create an account.
            lti_user = self.create_lti_user(lti_jwt_sub, lti_tool)
        return lti_user

    def create_lti_user(self, lti_jwt_sub, lti_tool):
        """
        Generate a new user on the edX platform with a random username and password,
        and associates that account with the LTI identity.
        """
        edx_user = self.create_native_user()

        lti_user = LtiUser(
            lti_tool=lti_tool,
            lti_jwt_sub=lti_jwt_sub,
            edx_user=edx_user
        )
        lti_user.save()
        return lti_user

    def authenticate(self, lti_user, lti_tool):
        return authenticate(
            username=lti_user.edx_user.username,
            lti_jwt_sub=lti_user.lti_jwt_sub,
            lti_tool=lti_tool
        )


class Lti1p3Backend(LtiBackend):

    def authenticate(self, username=None, lti_jwt_sub=None, lti_tool=None):
        try:
            edx_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        try:
            LtiUser.objects.get(
                edx_user_id=edx_user.id,
                lti_jwt_sub=lti_jwt_sub,
                lti_tool=lti_tool
            )
        except LtiUser.DoesNotExist:
            return None
        return edx_user
