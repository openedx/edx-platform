from django.conf.urls import url

from openedx.features.smart_referral.api_views import FilterContactsAPIView

urlpatterns = [
    url(
        r'^api/filter_contacts/$',
        FilterContactsAPIView.as_view(),
        name='filter_user_contacts'
    )
]
