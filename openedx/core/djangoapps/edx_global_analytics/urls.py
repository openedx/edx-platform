"""
URLs for the edX global analytics application.
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.ReceiveTokenView.as_view(), name='receive-token'),
]
