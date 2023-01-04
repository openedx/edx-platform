""" URLs for User Tours. """

from django.conf import settings
from django.urls import re_path, path

from lms.djangoapps.user_tours.v1.views import UserTourView, UserDiscussionsToursView


urlpatterns = [
    re_path(fr'^v1/{settings.USERNAME_PATTERN}$', UserTourView.as_view(), name='user-tours'),
    path('discussions-tours/', UserDiscussionsToursView.as_view(), name='discussion-tours'),
    path('discussions-tours/<int:tour_id>/', UserDiscussionsToursView.as_view(), name='update-discussion-tour')

]
