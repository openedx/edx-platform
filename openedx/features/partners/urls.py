"""
The urls for philu features app.
"""
from django.conf.urls import url

from .views import dashboard, register_user

urlpatterns = [
    url(r"^partner/(?P<slug>[0-9a-z]+)/$",  dashboard, name="partner_url"),
    url(r'^partner/(?P<slug>[0-9a-z]+)/register/$', register_user, name="partner_register"),
]
