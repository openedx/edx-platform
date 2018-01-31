from django.conf.urls import url

urlpatterns = [
    url(r'^v1/digital_books', DigitalBookView.as_view(), name='digitalbook'),
]