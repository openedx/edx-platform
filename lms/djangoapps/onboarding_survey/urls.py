from django.conf.urls import patterns, url

from onboarding_survey import views

# Additionally, we include login URLs for the browseable API.

urlpatterns = [
    url(r"^tell_us_more/$", views.tell_us_more, name="tell_us_more"),
    url(r"^interests/$", views.interests, name="interests"),
    url(r"^organization/$", views.organization, name="organization"),
    url(r"^get_country_names/$", views.get_country_names, name="get_country_names"),
    url(r"^get_languages/$", views.get_languages, name="get_languages"),
]
