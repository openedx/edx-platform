"""
Defines URLs for the course rating app.
"""

from django.conf.urls import include, url

urlpatterns = [
    url('', include('openedx.features.course_rating.api.v1.urls')),
]
