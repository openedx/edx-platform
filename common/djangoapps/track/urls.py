"""
URLs for track app
"""

from . import views
from .views import segmentio
from django.urls import path

urlpatterns = [
    path('event', views.user_track),
    path('segmentio/event', segmentio.segmentio_event),
]
