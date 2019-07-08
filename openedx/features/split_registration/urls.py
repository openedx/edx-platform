"""
The urls for on-boarding app.
"""
from django.conf.urls import url

from openedx.features.split_registration import views


urlpatterns = [

    url(r"^user-account/step1/$", views.user_info, name="step1"),  # signup step 1
    url(r"^user-account/step2/$", views.interests, name="step2"),  # signup step 2
    url(r"^user-account/step3/$", views.user_organization_role, name="step3"),  # signup step 3
    url(r"^user-account/step4/$", views.organization, name="step4"),  # signup step 4
    url(r"^user-account/step5/$", views.org_detail_survey, name="step5"),  # signup step 4

    url(r"^user-account/settings/$", views.update_account_settings, name="update_account"),

    url(r"^user-account/additional_information/$", views.user_info, name="additional_information_v2"),
    url(r"^user-account/interests/$", views.interests, name="update_interests_v2"),

    url(r"^user-organization/general/$", views.organization, name="update_organization_v2"),
    url(r"^user-organization/details/$", views.org_detail_survey, name="update_organization_details_v2"),

    url(r"^user-account/update_role/$", views.user_organization_role, name="update_role"),
]
