"""
Url setup for portfolio project.
"""
from django.conf.urls import url

from views import GenericTabView


urlpatterns = [
    url(
        r'^$',
        GenericTabView.as_view(),
        name='openedx.portfolio.generic_tab',
    ),
]
