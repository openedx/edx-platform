"""
URLs for the maintenance app.
"""
from django.conf.urls import url

from .views import ForcePublishCourseView, MaintenanceIndexView

urlpatterns = [
    url(r'^$', MaintenanceIndexView.as_view(), name='maintenance_index'),
    url(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name='force_publish_course'),
]
