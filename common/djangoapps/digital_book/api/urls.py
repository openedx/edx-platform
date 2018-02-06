from django.conf.urls import url

from .views import DigitalBookViewSet

urlpatterns = [
    url(r'^v1/digital_books',
        DigitalBookViewSet.as_view({
            'post': 'create',
        }),
        name='digitalbook'),
]