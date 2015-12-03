"""
URLs for badges API
"""
from django.conf.urls import patterns, url

from .views import UserBadgeAssertions
from openedx.core.djangoapps.user_api.urls import USERNAME_PATTERN

urlpatterns = patterns(
    'badges.api',
    url('^assertions/user/' + USERNAME_PATTERN + '/$', UserBadgeAssertions.as_view(), name='user_assertions'),
)
