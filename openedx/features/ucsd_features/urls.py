"""
Map urls to the relevant view handlers
"""

from django.conf.urls import url
from .views import email_support


urlpatterns = [
    url(
        r'^ucsd_support_email$',
        email_support,
        name='ucsd_support_email'
    )
]
