"""
Certificates API URLs.
"""


from django.conf.urls import include
from django.urls import path

app_name = 'certificates'
urlpatterns = [
    path('v0/', include('lms.djangoapps.certificates.apis.v0.urls')),
]
