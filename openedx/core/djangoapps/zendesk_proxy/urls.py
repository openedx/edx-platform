"""
Map urls to the relevant view handlers
"""

from django.conf.urls import url

from openedx.core.djangoapps.zendesk_proxy.v0.views import ZendeskPassthroughView as v0_view

urlpatterns = [
    url(r'^v0$', v0_view.as_view(), name='zendesk_proxy_v0'),
]
