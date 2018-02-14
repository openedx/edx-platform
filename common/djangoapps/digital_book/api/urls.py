from django.conf import settings
from django.conf.urls import url

from .views import DigitalBookViewSet
from .views import digital_book_about

urlpatterns = [
    url(r'^v1/digital_books$',
        DigitalBookViewSet.as_view({
            'post': 'create',
        }),
        name='digitalbook'),
    url(
        r'^v1/digital_books/{}/about$'.format(
            settings.BOOK_KEY_PATTERN,
        ),
        digital_book_about,
        name='about_digital_book',
    ),
]