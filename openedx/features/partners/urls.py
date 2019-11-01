"""
The urls for philu features app.
"""
from django.conf.urls import url

from .views import g2a_dashboard

urlpatterns = [
    url(r"^partners/g2a/$", g2a_dashboard, name="partners"),
]
