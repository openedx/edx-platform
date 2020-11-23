"""
URLs for bulk_email app
"""

from django.conf.urls import url
from django.conf import settings

from . import views

urlpatterns = [
    url(
        r'^email/optout/(?P<token>[a-zA-Z0-9-_=]+)/{}/$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        views.opt_out_email_updates,
        name='bulk_email_opt_out',
    ),
]
