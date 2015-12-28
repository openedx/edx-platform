"""
URLs for credential support views.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""

from django.conf.urls import url, patterns

from openedx.core.djangoapps.credentials.api import views

urlpatterns = patterns(
    '',
    url(
        r'^program_info/(?P<username>[^/]*)/(?P<program_id>\d+)$',
        views.ProgramCredentialInfoView.as_view(),
        name='program_info'
    ),
)
