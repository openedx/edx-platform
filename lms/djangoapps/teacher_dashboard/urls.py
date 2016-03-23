"""
URLs for the Labster Teacher Dashboard.
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^teacher_dashboard/?$', 'teacher_dashboard.views.dashboard_view', name='dashboard_view_handler'),
    url(r'^teacher/api/v0/data/?$', 'teacher_dashboard.views.teacher_dahsboard_handler'),
)
