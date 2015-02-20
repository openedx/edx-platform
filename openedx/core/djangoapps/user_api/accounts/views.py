from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework import status

from student.models import UserProfile
from openedx.core.djangoapps.user_api.accounts.serializers import AccountLegacyProfileSerializer, AccountUserSerializer
from openedx.core.lib.api.permissions import IsUserInUrlOrStaff

from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions


class AccountView(APIView):
    """
        **Use Cases**

            Get the user's account information.

        **Example Requests**:

            GET /api/user/v0/accounts/{username}/

        **Response Values**

            * username: The username associated with the account (not editable).

            * name: The full name of the user (not editable through this API).

            * email: The email for the user (not editable through this API).

            * date_joined: The date this account was created (not editable).

            * gender: null, "m", "f", or "o":

            * year_of_birth: null or integer year:

            * level_of_education: null or one of the following choices:

                * "p" signifying "Doctorate"
                * "m" signifying "Master's or professional degree"
                * "b" signifying "Bachelor's degree"
                * "a" signifying "Associate's degree"
                * "hs" signifying "Secondary/high school"
                * "jhs" signifying "Junior secondary/junior high/middle school"
                * "el" signifying "Elementary/primary school"
                * "none" signifying "None"
                * "o" signifying "Other"

             * language: null or name of preferred language

             * city: null or name of city

             * country: null or a Country corresponding to one of the ISO 3166-1 countries

             * mailing_address: null or textual representation of mailing address

             * goals: null or textual representation of goals

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def get(self, request, username):
        """
        GET /api/user/v0/accounts/{username}/
        """
        existing_user, existing_user_profile = self._get_user_and_profile(username)
        user_serializer = AccountUserSerializer(existing_user)
        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile)

        return Response(dict(user_serializer.data, **legacy_profile_serializer.data))

    def patch(self, request, username):
        """
        PATCH /api/user/v0/accounts/{username}/
        """
        existing_user, existing_user_profile = self._get_user_and_profile(username)

        user_serializer = AccountUserSerializer(existing_user, data=request.DATA)
        user_serializer.is_valid()
        user_serializer.save()

        legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=request.DATA)
        legacy_profile_serializer.is_valid()
        legacy_profile_serializer.save()

        return Response(dict(user_serializer.data, **legacy_profile_serializer.data))

    def _get_user_and_profile(self, username):
        """
        Helper method to return the legacy user and profile objects based on username.
        """
        try:
            existing_user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        existing_user_profile = UserProfile.objects.get(id=existing_user.id)

        return existing_user, existing_user_profile
