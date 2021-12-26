""" URLs for save_for_later """

from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('api/', include(('lms.djangoapps.save_for_later.api.urls', 'api'), namespace='api')),
]
