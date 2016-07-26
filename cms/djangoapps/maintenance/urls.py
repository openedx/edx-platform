"""
URLs for the maintenance app.
"""
from django.conf.urls import patterns, url

from .views import MaintenanceIndexView, ForcePublishCourseView


urlpatterns = patterns(
    '',
    url(r'^$', MaintenanceIndexView.as_view(), name='maintenance_index'),
    url(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name='force_publish_course'),
)
