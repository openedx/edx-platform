"""
Learner Dashboard API URLs.
"""

from django.urls import include, path

app_name = 'learner_dashboard'
urlpatterns = [
    path('v0/', include('lms.djangoapps.learner_dashboard.api.v0.urls')),
]
