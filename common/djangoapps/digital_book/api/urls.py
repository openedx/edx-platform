from django.conf import settings
from django.conf.urls import url

from .views import DigitalBookViewSet

urlpatterns = [
    url(r'^v1/digital_books$',
        DigitalBookViewSet.as_view({
            'post': 'create',
        }),
        name='digitalbook'),
    url(
        r'^v1/digital_books/{}/about$'.format(
            settings.COURSE_ID_PATTERN, #TODO: digitalbook pattern?
        ),
        DigitalBookViewSet.digital_book_about,
        name='about_digital_book',
    ),
]