"""
Urls for Job Board views
"""
from django.conf.urls import url

from .views import JobCreateView, JobDetailView, JobListView

urlpatterns = [
    url(r'^$', JobListView.as_view(), name='job_list'),
    url(r'^create/$', JobCreateView.as_view(), name='job_create'),
    url(r'^(?P<pk>[0-9]+)/$', JobDetailView.as_view(), name='job_detail'),
]
