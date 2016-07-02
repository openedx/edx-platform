from django.conf.urls import patterns, url

from appsembler.enrollment_api import views

urlpatterns = patterns(
    '',

    url(r'generate-codes', views.GenerateRegistrationCodesView.as_view(), name="generate_registration_codes_api"),
)
