from django.conf.urls import url

from .views import JobsListView, show_job_detail


urlpatterns = [
    url(r'^jobs/list/$', JobsListView.as_view(), name='job_list'),
    url(r'^jobs/list/[0-9]*$', show_job_detail, name='job_detail'),
]
