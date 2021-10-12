from django.conf import settings
from django.conf.urls import url

from .views import AboutUsView, BusinessView, MarketingCampaignPage, PartnerWithUsView, overview_tab_view

urlpatterns = [
    url(r'^about_us/?$', AboutUsView.as_view(), name="about_us"),
    url(
        r'^courses/{course_id}/overview/$'.format(course_id=settings.COURSE_ID_PATTERN),
        overview_tab_view,
        name='overview_tab_view'
    ),
    url(r'^business/$', BusinessView.as_view(), name='home-business'),
    url(r'^partner-with-us/$', PartnerWithUsView.as_view(), name='partner-with-us'),
    url(r'^workplace-harassment/$', MarketingCampaignPage.as_view(), name='workplace-harassment'),
]
