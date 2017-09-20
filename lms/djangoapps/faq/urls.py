from django.conf.urls import url
from lms.djangoapps.faq.views import get_faq, get_faq_title

urlpatterns = [
    url(r'^title', get_faq_title, name='title_faq'),
    url(r'', get_faq, name='custom_faq'),
]
