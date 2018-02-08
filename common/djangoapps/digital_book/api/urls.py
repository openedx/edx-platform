from django.conf.urls import url

from .views import DigitalBookViewSet

from digital_book.models import Dig

urlpatterns = [
    url(r'^v1/digital_books',
        DigitalBookViewSet.as_view({
            'post': 'create',
        }),
        name='digitalbook'),
]