"""
 API urls to communicate with nodeBB
"""
from django.conf.urls import url, patterns

from lms.djangoapps.philu_api.views import UpdateCommunityProfile

urlpatterns = patterns(
    'philu_api.views',
    url(r'profile/update/', UpdateCommunityProfile.as_view(), name='update_community_profile_update'),
)
