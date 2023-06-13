"""
URLs for the maintenance app.
"""

from django.urls import path, re_path

from .views import (
    AnnouncementCreateView,
    AnnouncementDeleteView,
    AnnouncementEditView,
    AnnouncementIndexView,
    ForcePublishCourseView,
    MaintenanceIndexView,
    V1LibCleanupView
)

app_name = 'cms.djangoapps.maintenance'

urlpatterns = [
    path('', MaintenanceIndexView.as_view(), name='maintenance_index'),
    re_path(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name='force_publish_course'),
    re_path(r'^announcements/(?P<page>\d+)?$', AnnouncementIndexView.as_view(), name='announcement_index'),
    path('announcements/create', AnnouncementCreateView.as_view(), name='announcement_create'),
    re_path(r'^announcements/edit/(?P<pk>\d+)?$', AnnouncementEditView.as_view(), name='announcement_edit'),
    path('announcements/delete/<int:pk>', AnnouncementDeleteView.as_view(), name='announcement_delete'),
    path('v1_lib_cleanup', V1LibCleanupView.as_view(), name='v1_library_cleanup'),
]
