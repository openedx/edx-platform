"""
Django URLs for cme_registration app
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'cme$', 'cme_registration.views.cme_register_user', name='cme_register_user'),
    url(r'cme_create_account', 'cme_registration.views.cme_create_account', name='cme_create_account'),
)
