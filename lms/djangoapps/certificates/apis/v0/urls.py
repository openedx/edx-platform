"""
Certificates API v0 URLs.
"""
from django.conf import settings
from django.conf.urls import include, url

from lms.djangoapps.certificates.apis.v0 import views

CERTIFICATES_URLS = ([
    url(
        r'^{username}/courses/{course_id}/$'.format(
            username=settings.USERNAME_PATTERN,
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.CertificatesDetailView.as_view(), name='detail'
    ),
], 'certificates')

app_name = 'v0'
urlpatterns = [
    url(r'^certificates/', include(CERTIFICATES_URLS)),
]
