from django.conf.urls import url

from .views import add_job, JobDetailView, JobListView

urlpatterns = [
    url(r'$', JobListView.as_view(), name='job_list'),
    url(r'add/$', add_job, name='add_job'),
    url(r'(?P<pk>[0-9]+)/$', JobDetailView.as_view(), name='job_detail'),
]
