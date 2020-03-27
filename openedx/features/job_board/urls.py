from django.conf.urls import url

from .views import list_jobs, show_job_detail


urlpatterns = [
    url(r'^jobs/list/$', list_jobs, name='job_list'),
    url(r'^jobs/list/[0-9]$', list_jobs, name='job_detail'),
]
