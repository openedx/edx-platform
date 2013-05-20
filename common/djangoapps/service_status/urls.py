"""
Django URLs for service status app
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'service_status.views.index', name='status.service.index'),
    url(r'^celery/$', 'service_status.views.celery_status',
        name='status.service.celery.status'),
    url(r'^celery/ping/$', 'service_status.views.celery_ping',
        name='status.service.celery.ping'),
)
