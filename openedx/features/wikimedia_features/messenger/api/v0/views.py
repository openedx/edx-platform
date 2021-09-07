"""
Views for Messenger v0 API(s)
"""
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from openedx.features.wikimedia_features.messenger.models import Inbox, Message
from openedx.features.wikimedia_features.messenger.api.v0.serializers import (
    InboxSerializer, MessageSerializer, UserSerializer, BulkMessageSerializer
)


class MesssengerResultsSetPagination(PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):
        response = super(MesssengerResultsSetPagination, self).get_paginated_response(data)
        response.data['num_pages'] = self.page.paginator.num_pages
        response.data['count']: self.page.paginator.count
        return response


class UserSearchView(viewsets.ReadOnlyModelViewSet):
    """
    Search user's username containing given query string.

    GET /messenger/api/v0/user/?search=name
    Return list of users
    [
        {
            "username": "username1"
        },
        ...
    ]
    """
    serializer_class = UserSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        if query:
            return User.objects.filter(
                username__icontains=query
            ).exclude(username=self.request.user.username)
        raise NotFound(_('Search query param is required.'))


class InboxView(viewsets.ModelViewSet):
    """
    Returns list of all inbox messages of request user
    Get /messenger/api/v0/inbox/
    {
        "count": 2,
        "next": null,
        "previous": null,
        "num_pages": 1
        "results": [
            {
                "id": 37,
                "with_user": "staff",
                "last_message": "hello, how are you d...",
                "unread_count": 0,
                "with_user_img": "profile_image_url"
            },
           ...
        ],
    }

    Retrieve single inbox message object
    Get /messenger/api/v0/inbox/pk
    {
        "id": 37,
        "with_user": "staff",
        "last_message": "hello, how are you d...",
        "unread_count": 0,
        "with_user_img": "profile_image_url"
    }
    ```

    Update inbox message object
    PATCH /messenger/api/v0/inbox/pk
    {
        "unread_count": 2,
    }
    ```

    Note:
    - user can view and update only his inbox resources

    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InboxSerializer
    pagination_class = MesssengerResultsSetPagination

    def get_queryset(self):
        return Inbox.user_inbox.find_all(self.request.user)


class ConversationView(viewsets.ModelViewSet):
    """
    Return conversation between two users -> All messages sent or received between request.user and
    user with given username.
    GET /conversation/?with_user=username2
    [
        {
            "id": 2093,
            "sender": "honor",
            "receiver": "edx",
            "message": "what's the progress on task1 ?",
            "created": "08/31/21-01:09 PM",
            "sender_img": "sender_profile_image url"
        },
        ...
    ]
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = MessageSerializer
    pagination_class = MesssengerResultsSetPagination

    def get_queryset(self):
        with_user = self.request.GET.get('with_user', '')
        if not with_user:
            raise NotFound(_('with_user param is required.'))

        try:
            with_user = User.objects.get(username=with_user)
            return Message.chat.history(self.request.user, with_user)
        except User.DoesNotExist:
            raise NotFound(_('User with username: {} does not exist.'.format(with_user)))


class MessageCreateView(generics.CreateAPIView):
    """
    Create Single Message -
    POST /messenger/api/v0/message/
    {
        "receiver": "receiver_username",
        "message": "sample message text"
    }
    Return newly created message
    {
        "id": 2092,
        "sender": "sender_username",
        "receiver": "receiver_username",
        "message": "sample message text",
        "created": "08/31/21-01:08 PM",
        "sender_img": "sender_profile_image_url"
    }

    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MessageSerializer


class BulkMessageView(viewsets.ViewSet):
    """
    Create Bulk messages from request.user

    POST /messenger/api/v0/bulk_message/
    POST DATA: {
        "receivers": [username1, username2]
        "message": "message sample text"
    }
    """
    serializer_class = BulkMessageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def bulk_message(self, *ags, **kwargs):
        serializer = BulkMessageSerializer(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            created_msgs = serializer.bulk_create(request=self.request)
            return Response(
                data=InboxSerializer(
                    Inbox.objects.filter(last_message__in=created_msgs),
                    context={'request': self.request},
                    many=True
                ).data,
                status=status.HTTP_200_OK
            )
