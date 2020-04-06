from django.conf.urls import url

from .views import JobDetailView, JobListView

urlpatterns = [
    url(r'^jobs/$', JobListView.as_view(), name='job_list'),
    url(r'^jobs/(?P<pk>[0-9]+)/$', JobDetailView.as_view(), name='job_detail'),
]
