from django.conf.urls import url

from openedx.features.smart_referral.api_views import FilterContactsAPIView

from .views import send_initial_emails


urlpatterns = [
    url(r'^initial_emails/$', send_initial_emails, name='initial_referral_emails'),
    url(
        r'^api/filter_contacts/$',
        FilterContactsAPIView.as_view(),
        name='filter_user_contacts'
    )
]
