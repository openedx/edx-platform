from django.conf.urls import patterns, url

from appsembler.jitterbit_api import views

urlpatterns = patterns(
    '',
    url(r'^v1/accounts/batch', views.GetBatchUserDataView.as_view(), name="get_batch_user_data"),
    url(r'^v1/enrollment/batch', views.GetBatchEnrollmentDataView.as_view(), name="get_batch_enrollment_data"),

)