"""
CCX API URLs.
"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v0/', include('lms.djangoapps.ccx.api.v0.urls', namespace='v0')),
]
