"""
Views for groups info API
"""

from rest_framework import generics, status, mixins
from rest_framework.response import Response
from django.conf import settings
import facebook

from ...utils import mobile_view
from . import serializers


@mobile_view()
class Groups(generics.CreateAPIView, mixins.DestroyModelMixin):
    """
    **Use Case**

        An API to Create or Delete course groups.

        Note: The Delete is not invoked from the current version of the app
        and is used only for testing with facebook dependencies.

    **Creation Example request**:

        POST /api/mobile/v0.5/social/facebook/groups/

        Parameters: name : string,
                    description : string,
                    privacy : open/closed

    **Creation Response Values**

        {"id": group_id}

    **Deletion Example request**:

        DELETE /api/mobile/v0.5/social/facebook/groups/<group_id>

    **Deletion Response Values**

        {"success" : "true"}

    """
    serializer_class = serializers.GroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            app_groups_response = facebook_graph_api().request(
                settings.FACEBOOK_API_VERSION + '/' + settings.FACEBOOK_APP_ID + "/groups",
                post_args=request.POST.dict()
            )
            return Response(app_groups_response)
        except facebook.GraphAPIError, ex:
            return Response({'error': ex.result['error']['message']}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Deletes the course group.
        """
        try:
            return Response(
                facebook_graph_api().request(
                    settings.FACEBOOK_API_VERSION + '/' + settings.FACEBOOK_APP_ID + "/groups/" + kwargs['group_id'],
                    post_args={'method': 'delete'}
                )
            )
        except facebook.GraphAPIError, ex:
            return Response({'error': ex.result['error']['message']}, status=status.HTTP_400_BAD_REQUEST)


@mobile_view()
class GroupsMembers(generics.CreateAPIView, mixins.DestroyModelMixin):
    """
    **Use Case**

        An API to Invite and Remove members to a group

        Note: The Remove is not invoked from the current version
        of the app and is used only for testing with facebook dependencies.

    **Invite Example request**:

        POST /api/mobile/v0.5/social/facebook/groups/<group_id>/member/

        Parameters: members : int,int,int...


    **Invite Response Values**

        {"member_id" : success/error_message}
        A response with each member_id and whether or not the member was added successfully.
        If the member was not added successfully the Facebook error message is provided.

    **Remove Example request**:

        DELETE /api/mobile/v0.5/social/facebook/groups/<group_id>/member/<member_id>

    **Remove Response Values**

        {"success" : "true"}
    """
    serializer_class = serializers.GroupsMembersSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        graph = facebook_graph_api()
        url = settings.FACEBOOK_API_VERSION + '/' + kwargs['group_id'] + "/members"
        member_ids = serializer.data['member_ids'].split(',')
        response = {}
        for member_id in member_ids:
            try:
                if 'success' in graph.request(url, post_args={'member': member_id}):
                    response[member_id] = 'success'
            except facebook.GraphAPIError, ex:
                response[member_id] = ex.result['error']['message']
        return Response(response, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Deletes the member from the course group.
        """
        try:
            return Response(
                facebook_graph_api().request(
                    settings.FACEBOOK_API_VERSION + '/' + kwargs['group_id'] + "/members",
                    post_args={'method': 'delete', 'member': kwargs['member_id']}
                )
            )
        except facebook.GraphAPIError, ex:
            return Response({'error': ex.result['error']['message']}, status=status.HTTP_400_BAD_REQUEST)


def facebook_graph_api():
    """
    Returns the result from calling Facebook's Graph API with the app's access token.
    """
    return facebook.GraphAPI(facebook.get_app_access_token(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET))
