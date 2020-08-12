""" URL definitions for waffle utils. """

from django.conf.urls import url
from openedx.core.djangoapps.waffle_utils.views import ToggleStateView

urlpatterns = [
    url(r'^state/', ToggleStateView.as_view(), name="toggle_state"),
]
