"""
URLs for friends API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import FriendsInCourse

urlpatterns = patterns(
    'mobile_api.social_facebook.friends.views',
    url(
        r'^course/{}$'.format(settings.COURSE_ID_PATTERN),
        FriendsInCourse.as_view(),
        name='friends-in-course'
    ),
)
