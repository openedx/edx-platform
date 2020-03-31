from django.conf.urls import url

from .views import JobsListView


urlpatterns = [
    url(r'^jobs/list/$', JobsListView.as_view(), name='job_list'),
    url(r'^jobs/list/[0-9]$', JobsListView.as_view(), name='job_detail'),
]
