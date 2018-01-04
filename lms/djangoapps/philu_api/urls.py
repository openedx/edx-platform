"""
 API urls to communicate with nodeBB
"""
from django.conf.urls import url, patterns

from lms.djangoapps.philu_api.views import UpdateCommunityProfile, get_user_chat, mark_user_chat_read

urlpatterns = patterns(
    'philu_api.views',
    url(r'profile/update/', UpdateCommunityProfile.as_view(), name='update_community_profile_update'),
    url(r'profile/chats/?$', get_user_chat, name='get_user_chat'),
    url(r'profile/chats/mark/?$', mark_user_chat_read, name='mark_user_chat_read'),
)
