"""
Views for users sharing preferences
"""

from rest_framework import generics, status
from rest_framework.response import Response

from openedx.core.djangoapps.user_api.api.profile import preference_info, update_preferences
from ..utils import mobile_view
from lms.djangoapps.mobile_api.preferences import serializers


@mobile_view()
class UserSharing(generics.ListCreateAPIView):
    """
    **Use Case**

        An API to retrieve or update the users social sharing settings

    **GET Example request**:

        GET /api/mobile/v0.5/settings/preferences/

    **GET Response Values**

        {'share_with_facebook_friends': 'True'}

    **POST Example request**:

        POST /api/mobile/v0.5/settings/preferences/

        paramters: share_with_facebook_friends : True

    **POST Response Values**

        {'share_with_facebook_friends': 'True'}

    """
    serializer_class = serializers.UserSharingSerializar

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA, files=request.FILES)
        if serializer.is_valid():
            value = serializer.object['share_with_facebook_friends']
            try:
                update_preferences(request.user.username, share_with_facebook_friends=value)
            except facebook.GraphAPIError, ex:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=ex.data)
            preferences = preference_info(request.user.username)
            response = {'share_with_facebook_friends': preferences['share_with_facebook_friends']} \
                if ('share_with_facebook_friends' in preferences) else {}
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        preferences = preference_info(request.user.username)
        response = {'share_with_facebook_friends': preferences['share_with_facebook_friends']} \
            if ('share_with_facebook_friends' in preferences) else {}
        return Response(response)
