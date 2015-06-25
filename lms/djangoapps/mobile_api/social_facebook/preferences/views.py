"""
Views for users sharing preferences
"""

from rest_framework import generics, status
from rest_framework.response import Response

from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences, set_user_preference
from ...utils import mobile_view
from . import serializers


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
            set_user_preference(request.user, "share_with_facebook_friends", value)
            return self.get(request, *args, **kwargs)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        preferences = get_user_preferences(request.user)
        response = {'share_with_facebook_friends': preferences.get('share_with_facebook_friends', 'False')}
        return Response(response)
