"""
API v1 URLs.
"""
from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^completion-batch', views.CompletionBatchView.as_view(), name='completion-batch'),
]
