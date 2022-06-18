"""
URL definitions for the CSRF API endpoints.
"""

from django.urls import include, re_path


urlpatterns = [
    re_path(r'^v1/', include('csrf.api.v1.urls'), name='csrf_api_v1'),
]
