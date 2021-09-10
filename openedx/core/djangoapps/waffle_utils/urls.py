""" URL definitions for waffle utils. """
from openedx.core.djangoapps.waffle_utils.views import ToggleStateView
from django.urls import path

urlpatterns = [
    path('v0/state/', ToggleStateView.as_view(), name="toggle_state"),
]
