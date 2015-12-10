"""
URLs for the credentials support in LMS and Studio.
"""

from django.conf.urls import url

from openedx.core.djangoapps.credentials.api.v1 import views

urlpatterns = [
    url(r'^v1/user_credentials/$', views.GenerateProgramsCredentialView.as_view()),
]
