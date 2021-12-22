"""
Defines URLs for Calendar Sync.
"""

from .views.calendar_sync import CalendarSyncView
from django.urls import path

urlpatterns = [
    path('calendar_sync', CalendarSyncView.as_view(),
         name='openedx.calendar_sync',
         ),
]
