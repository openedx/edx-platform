from django.conf.urls import url
from lms.djangoapps.faq.views import get_faq

urlpatterns = [
    url(r'', get_faq, name='custom_faq'),
]
