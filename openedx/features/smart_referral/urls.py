from django.conf.urls import url

from .views import send_initial_emails

urlpatterns = [
    url(r'^initial_emails/$', send_initial_emails, name='initial_referral_emails'),
]
