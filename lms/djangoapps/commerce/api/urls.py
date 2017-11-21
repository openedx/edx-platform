"""
API URLs.
"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v0/', include('lms.djangoapps.commerce.api.v0.urls', namespace='v0')),
    url(r'^v1/', include('lms.djangoapps.commerce.api.v1.urls', namespace='v1')),
]
