"""
URLs for the CSRF application.
"""

from django.urls import include, re_path


urlpatterns = [
    re_path(r'^csrf/api/', include('csrf.api.urls'), name='csrf_api'),
]
