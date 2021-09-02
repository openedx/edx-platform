"""
Urls for Messenger
"""
from django.conf.urls import include, url

from  openedx.features.wikimedia_features.messenger.views import render_messenger_home


urlpatterns = [
    url(
        r'^$',
        render_messenger_home,
        name='messenger_home'
    ),
    url(
        r'^api/v0/',
        include('openedx.features.wikimedia_features.messenger.api.v0.urls', namespace='messenger_api_v0')
    ),
]
