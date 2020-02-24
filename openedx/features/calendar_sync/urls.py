"""
Defines URLs for Calendar Sync.
"""


from django.conf.urls import url

from .views.calendar_sync import CalendarSyncView

urlpatterns = [
    url(
        r'^calendar_sync$',
        CalendarSyncView.as_view(),
        name='openedx.calendar_sync',
    ),
]
