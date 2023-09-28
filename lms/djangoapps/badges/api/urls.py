"""
URLs for badges API
"""


from django.conf import settings
from django.urls import re_path

from .views import UserBadgeAssertions

urlpatterns = [
    re_path('^assertions/user/' + settings.USERNAME_PATTERN + '/$',
            UserBadgeAssertions.as_view(), name='user_assertions'),
]
