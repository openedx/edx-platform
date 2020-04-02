from django.conf.urls import url

from .views import JobListView, show_job_detail

urlpatterns = [
    url(r'^jobs/$', JobListView.as_view(), name='job_list'),
    url(r'^jobs/[0-9]+$', show_job_detail, name='job_detail'),
]
