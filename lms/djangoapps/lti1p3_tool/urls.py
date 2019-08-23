from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import url

from .views import login, launch

urlpatterns = [
    url(r'^login/?$', login, name="lti1p3_tool_login"),
    url(r'^launch/?$', launch, name="lti1p3_tool_launch"),
    url(r'^launch/{block_id}/?$'.format(block_id=settings.USAGE_ID_PATTERN),
        launch, name="lti1p3_tool_launch_block"),
]
