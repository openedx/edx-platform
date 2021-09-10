"""
Certificates API v0 URLs.
"""


from django.conf import settings
from django.conf.urls import include

from lms.djangoapps.certificates.apis.v0 import views
from django.urls import path, re_path

CERTIFICATES_URLS = ([
    re_path(
        r'^{username}/courses/{course_id}/$'.format(
            username=settings.USERNAME_PATTERN,
            course_id=settings.COURSE_ID_PATTERN
        ),
        views.CertificatesDetailView.as_view(), name='detail'
    ),
    re_path(
        r'^{username}/$'.format(
            username=settings.USERNAME_PATTERN
        ),
        views.CertificatesListView.as_view(), name='list'
    ),
], 'certificates')

app_name = 'v0'
urlpatterns = [
    path('certificates/', include(CERTIFICATES_URLS)),
]
