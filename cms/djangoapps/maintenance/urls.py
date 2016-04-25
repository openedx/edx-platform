"""
URLs for the maintenance app.
"""
from django.conf.urls import patterns, url

from .views import MaintenanceIndexView, ShowOrphansView, DeleteOrphansView, ExportCourseView, \
    ImportCourseView, DeleteCourseView, ForcePublishCourseView


urlpatterns = patterns(
    '',
    url(r'^$', MaintenanceIndexView.as_view(), name="maintenance"),
    url(r'^show_orphans/?$', ShowOrphansView.as_view(), name="show_orphans"),
    url(r'^delete_orphans/?$', DeleteOrphansView.as_view(), name="delete_orphans"),
    url(r'^export_course/?$', ExportCourseView.as_view(), name="export_course"),
    url(r'^import_course/?$', ImportCourseView.as_view(), name="import_course"),
    url(r'^delete_course/?$', DeleteCourseView.as_view(), name="delete_course"),
    url(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name="force_publish_course"),
)
