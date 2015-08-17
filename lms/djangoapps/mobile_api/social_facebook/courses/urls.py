"""
URLs for courses API
"""
from django.conf.urls import patterns, url

from .views import CoursesWithFriends

urlpatterns = patterns(
    'mobile_api.social_facebook.courses.views',
    url(
        r'^friends$',
        CoursesWithFriends.as_view(),
        name='courses-with-friends'
    ),
)
