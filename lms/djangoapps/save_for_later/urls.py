""" URLs for save_for_later """

from django.conf.urls import include, url

urlpatterns = [
    url(r'^api/', include(('lms.djangoapps.save_for_later.api.urls', 'api'), namespace='api')),
]
