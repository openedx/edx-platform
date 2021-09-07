"""
Urls for Messenger v0 API(s)
"""
from django.conf.urls import url

from openedx.features.wikimedia_features.messenger.api.v0.views import (
    InboxView, ConversationView, MessageCreateView, UserSearchView, BulkMessageView
)

app_name = 'messenger_api_v0'


urlpatterns = [
    url(
        r'^bulk_message/$',
        BulkMessageView.as_view({
            'post': 'bulk_message'
        }),
        name="bulk_message"
    ),
    url(
        r'^user/$',
        UserSearchView.as_view({
            'get': 'list'
        }),
        name="user_search"
    ),
    url(
        r'^inbox/$',
        InboxView.as_view({
            'get': 'list'
        }),
        name="user_inbox_list"
    ),
    url(
        r'^inbox/(?P<pk>\d+)/$',
        InboxView.as_view({
            'patch': 'partial_update',
            'get': 'retrieve'
        }),
        name="user_inbox_detail"
    ),
    url(
        r'^conversation/$',
        ConversationView.as_view({
            'get': 'list',
        }),
        name="conversation_list"
    ),
    url(
        r'^message/$',
        MessageCreateView.as_view(),
        name="message_create"
    ),
]
