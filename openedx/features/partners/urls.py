"""
The urls for philu features app.
"""
from django.conf.urls import url

from .views import dashboard

urlpatterns = [
    url(r"^partner/(?P<slug>[0-9a-f]{32})/$",  dashboard, name="partner_url"),
]
