"""
Api URLs.
"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('lms.djangoapps.completion.api.v1.urls', namespace='v1')),
]
