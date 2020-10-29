"""
URLs for the maintenance app.
"""


from django.conf.urls import url

from .views import (
    AnnouncementCreateView,
    AnnouncementDeleteView,
    AnnouncementEditView,
    AnnouncementIndexView,
    ForcePublishCourseView,
    MaintenanceIndexView
)

app_name = 'cms.djangoapps.maintenance'

urlpatterns = [
    url(r'^$', MaintenanceIndexView.as_view(), name='maintenance_index'),
    url(r'^force_publish_course/?$', ForcePublishCourseView.as_view(), name='force_publish_course'),
    url(r'^announcements/(?P<page>\d+)?$', AnnouncementIndexView.as_view(), name='announcement_index'),
    url(r'^announcements/create$', AnnouncementCreateView.as_view(), name='announcement_create'),
    url(r'^announcements/edit/(?P<pk>\d+)?$', AnnouncementEditView.as_view(), name='announcement_edit'),
    url(r'^announcements/delete/(?P<pk>\d+)$', AnnouncementDeleteView.as_view(), name='announcement_delete'),
]
