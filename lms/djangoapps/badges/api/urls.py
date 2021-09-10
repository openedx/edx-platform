"""
URLs for badges API
"""


from django.conf import settings

from .views import UserBadgeAssertions
from django.urls import re_path

urlpatterns = [
    re_path('^assertions/user/' + settings.USERNAME_PATTERN + '/$', UserBadgeAssertions.as_view(), name='user_assertions'),
]
