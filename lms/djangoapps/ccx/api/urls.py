"""
CCX API URLs.
"""


from django.conf.urls import include
from django.urls import path

app_name = 'ccx_api'
urlpatterns = [
    path('v0/', include('lms.djangoapps.ccx.api.v0.urls')),
]
