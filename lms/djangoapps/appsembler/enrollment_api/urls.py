from django.conf.urls import patterns, url

from appsembler.enrollment_api import views

urlpatterns = patterns(
    '',
    url(r'generate-codes', views.GenerateRegistrationCodesView.as_view(), name="generate_registration_codes_api"),
    url(r'enroll-user-with-code', views.EnrollUserWithEnrollmentCodeView.as_view(), name="enroll_use_with_code_api"),
    url(r'enrollment-code-status', views.EnrollmentCodeStatusView.as_view(), name="enrollment_code_status_api"),
)
