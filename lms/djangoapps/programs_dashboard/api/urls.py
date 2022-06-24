"""
Programs Dashboard API URLs.
"""

from django.urls import include, path

app_name = 'programs_dashboard'

urlpatterns = [
    path('v0/', include('lms.djangoapps.programs_dashboard.api.v0.urls')),
]
