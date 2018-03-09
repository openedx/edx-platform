"""
 API urls to communicate with nodeBB
"""
from django.conf.urls import url, patterns

from lms.djangoapps.philu_api.views import PlatformSyncService, \
    get_user_chat, mark_user_chat_read, get_user_data

urlpatterns = patterns(
    'philu_api.views',
    url(r'platform/sync/service/', PlatformSyncService.as_view(), name='get_shared_data'),
    url(r'profile/update/', PlatformSyncService.as_view(), name='update_community_profile_update'),
    url(r'profile/chats/?$', get_user_chat, name='get_user_chat'),
    url(r'profile/data/?$', get_user_data, name='get_user_data'),
    url(r'profile/chats/mark/?$', mark_user_chat_read, name='mark_user_chat_read'),
)
