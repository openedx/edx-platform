"""
URLs for the Labster Teacher Dashboard.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
        '',
        url(r'^teacher_dashboard/?$', 'teacher_dashboard.views.dashboard_view', name='dashboard_view_handler'),

        # Api calls
        url(r'^licenses/?$', 'teacher_dashboard.views.licenses_api_call'),
        url(r'^licenses/(?P<license_pk>[a-zA-Z0-9\-]+)/simulations/?$', 'teacher_dashboard.views.simulations_api_call'),
        url(
                r'^licenses/(?P<license_pk>[a-zA-Z0-9\-]+)/simulations/(?P<simulation_pk>[a-zA-Z0-9]+)/students/?$',
                'teacher_dashboard.views.students_api_call'
        ),
)
