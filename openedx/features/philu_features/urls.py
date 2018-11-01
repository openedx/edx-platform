"""
The urls for philu features app.
"""
from django.conf.urls import url

from openedx.features.philu_features import views

urlpatterns = [
    url(r"^certificates/$", views.student_certificates, name="certificates"),
]
