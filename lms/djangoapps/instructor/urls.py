"""
URLs for the instructor dashboard
"""

from django.conf.urls import url, patterns

from .views.instructor_dashboard import InstructorDashboardComponentView


urlpatterns = patterns(
    'lms.djangoapps.instructor.views.instructor_dashboard',

    url(
        r'instructor_dashboard_component$',
        InstructorDashboardComponentView.as_view(),
        name='instructor_dashboard_component',
    ),
    url(r'', 'instructor_dashboard_2', name='instructor_dashboard'),
)
