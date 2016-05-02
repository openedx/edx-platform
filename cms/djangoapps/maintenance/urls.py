"""
URLs for the maintenance app.
"""
from django.conf.urls import patterns, url

from .views import MaintenanceIndexView, ShowOrphansView, ForcePublishCourseView


urlpatterns = patterns(
    '',
    url(r'^$', MaintenanceIndexView.as_view(), name="maintenance"),
    url(r'^show_orphans/?$', ShowOrphansView.as_view(), name="show_orphans"),
    url(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name="force_publish_course"),
)
