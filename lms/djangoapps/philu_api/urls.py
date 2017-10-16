"""
 API urls to communicate with nodeBB
"""
from django.conf.urls import url, patterns

urlpatterns = patterns(
    'philu_api.views',
    url(r'profile/update/', 'update_community_profile_update', name='update_community_profile_update'),
)
