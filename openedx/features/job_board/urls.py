from django.conf.urls import url

from .views import add_job, list_jobs, show_job_detail


urlpatterns = [
    url(r'list/$', list_jobs, name='job_list'),
    url(r'add/$', add_job, name='add_job'),
    url(r'[0-9]+/$', show_job_detail, name='job_detail'),
]
