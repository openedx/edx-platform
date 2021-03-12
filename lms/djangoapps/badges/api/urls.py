"""
URLs for badges API
"""


from django.conf import settings
from django.conf.urls import url

from .views import UserBadgeAssertions

urlpatterns = [
    url('^assertions/user/' + settings.USERNAME_PATTERN + '/$', UserBadgeAssertions.as_view(), name='user_assertions'),
]
