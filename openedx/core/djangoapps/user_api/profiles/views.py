"""
NOTE: this API is WIP and has not yet been approved. Do not use this API without talking to Christina or Andy.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/User+API
"""
from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework import permissions

from ..accounts.views import AccountView
from ..api.account import AccountUserNotFound
from ..models import UserPreference

from . import PROFILE_VISIBILITY_PREF_KEY, ALL_USERS_VISIBILITY


class ProfileView(APIView):
    """
        **Use Cases**

            Get the user's public profile information.

        **Example Requests**:

            GET /api/user/v0/profiles/{username}/[?include_all={true | false}]

        **Response Values for GET**

            Returns the same responses as for the AccountView API for the
            subset of fields that have been configured to be in a profile.
            The fields are additionally filtered based upon the user's
            specified privacy permissions.

            If the parameter 'include_all' is passed as 'true' then a user
            can receive all fields for their own account, ignoring
            any field visibility preferences. If the parameter is not
            specified or if the user is requesting information for a
            different account then the privacy filtering will be applied.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username):
        """
        GET /api/user/v0/profiles/{username}/[?include_all={true | false}]

        Note:
          The include_all query parameter will only be honored if the user is making
          the request for their own username. It defaults to false, but if true
          then all the profile fields will be returned even for a user with
          a private profile.
        """
        if request.user.username == username:
            include_all_fields = self.request.QUERY_PARAMS.get('include_all') == 'true'
        else:
            include_all_fields = False
        try:
            profile_settings = ProfileView.get_serialized_profile(
                username,
                settings.PROFILE_CONFIGURATION,
                include_all_fields=include_all_fields,
            )
        except AccountUserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(profile_settings)

    @staticmethod
    def get_serialized_profile(username, configuration=None, include_all_fields=False):
        """Returns the user's public profile settings serialized as JSON.

        The fields returned are by default governed by the user's privacy preference.
        If the user has a private profile, then only the fields that are always
        public are returned. If the user is sharing their profile with all users
        then all profile fields are returned.

        Note:
          This method does not perform authentication so it is up to the caller
          to ensure that only edX users can access the profile. In addition, only
          the user themselves should be able to access all fields of a private
          profile through 'include_all_fields' being true.

        Args:
          username (str): The username for the desired account.
          configuration (dict): A dictionary specifying three profile configuration settings:
            default_visibility: the default visibility level for user's with no preference
            all_fields: the list of all fields that can be shown on a profile
            public_fields: the list of profile fields that are public
          include_all_fields (bool): If true, ignores the user's privacy setting.

        Returns:
           A dict containing each of the user's profile fields.

        Raises:
           AccountUserNotFound: raised if there is no account for the specified username.
        """
        if not configuration:
            configuration = settings.PROFILE_CONFIGURATION
        account_settings = AccountView.get_serialized_account(username)
        profile = {}
        privacy_setting = ProfileView._get_user_profile_privacy(username, configuration)
        if include_all_fields or privacy_setting == ALL_USERS_VISIBILITY:
            field_names = configuration.get('all_fields')
        else:
            field_names = configuration.get('public_fields')
        for field_name in field_names:
            profile[field_name] = account_settings.get(field_name, None)
        return profile

    @staticmethod
    def _get_user_profile_privacy(username, configuration):
        """
        Returns the profile privacy preference for the specified user.
        """
        user = User.objects.get(username=username)
        profile_privacy = UserPreference.get_preference(user, PROFILE_VISIBILITY_PREF_KEY)
        return profile_privacy if profile_privacy else configuration.get('default_visibility')
