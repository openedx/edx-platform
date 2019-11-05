"""
The urls for philu features app.
"""
from django.conf.urls import url

from .views import g2a_dashboard

urlpatterns = [
    url(r"^partners/give2asia/$", g2a_dashboard, name="partners"),
]
