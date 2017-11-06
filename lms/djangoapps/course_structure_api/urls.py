"""
Course Structure API URI specification.

Patterns here should simply point to version-specific patterns.
"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v0/', include('course_structure_api.v0.urls', namespace='v0'))
]
