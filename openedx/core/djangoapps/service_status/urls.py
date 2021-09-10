"""
Django URLs for service status app
"""
from openedx.core.djangoapps.service_status.views import celery_ping, celery_status, index
from django.urls import path

urlpatterns = [
    path('', index, name='status.service.index'),
    path('celery/', celery_status, name='status.service.celery.status'),
    path('celery/ping/', celery_ping, name='status.service.celery.ping'),
]
