"""
All test for homepage app urls
"""
from django.conf.urls import url
from django.views.generic.base import RedirectView

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='https://philanthropyu.org'), name='redirect-lms-homepage'),
]
