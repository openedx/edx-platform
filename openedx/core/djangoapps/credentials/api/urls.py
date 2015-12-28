"""
URLs for credential support views.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import patterns, url, include

from openedx.core.djangoapps.credentials.api import views


router = DefaultRouter()  # pylint: disable=invalid-name
router.register(
    r'program_credential_info/',
    views.ProgramCredentialInfoView,
    base_name='program_credentials_info'
)

urlpatterns = router.urls
