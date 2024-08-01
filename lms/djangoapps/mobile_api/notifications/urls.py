"""
URLs for the mobile_api.notifications APIs.
"""
from django.urls import path
from .views import GCMDeviceViewSet


CREATE_GCM_DEVICE = GCMDeviceViewSet.as_view({'post': 'create'})


urlpatterns = [
    path('create-token/', CREATE_GCM_DEVICE, name='gcmdevice-list'),
]
