"""
The urls for on-boarding app.
"""
from django.conf.urls import url

from lms.djangoapps.onboarding import views


urlpatterns = [
    url(r"^onboarding/recommendations/$", views.recommendations, name="recommendations"),
    url(r"^onboarding/user_info/$", views.user_info, name="user_info"),  # signup step 1
    url(r"^onboarding/interests/$", views.interests, name="interests"),  # signup step 2
    url(r"^onboarding/organization/$", views.organization, name="organization"),  # signup step 3
    url(r"^onboarding/get_country_names/$", views.get_country_names, name="get_country_names"),
    url(r"^onboarding/get_languages/$", views.get_languages, name="get_languages"),
    url(r"^myaccount/settings/$", views.update_account_settings, name="update_account_settings"),
    url(r"^myaccount/additional_information/$", views.user_info, name="additional_information"),
    url(r"^myaccount/interests/$", views.interests, name="update_interests"),
    url(r'^myaccount/organization/$', views.organization, name='myaccount_organization'),
    url(r'^myaccount/organization_detail/$', views.org_detail_survey, name='myaccount_organization_detail'),
    url(r"^organization/general/$", views.organization, name="update_organization"),
    url(r"^organization/details/$", views.org_detail_survey, name="update_organization_details"),
    url(r"^onboarding/get_organizations/$", views.get_organizations, name="get_organizations"),
    url(r"^onboarding/suggest_org_admin/$", views.suggest_org_admin, name="suggest_org_admin"),
    url(r"^onboarding/get_currencies/$", views.get_currencies, name="get_currencies"),
    url(r"^onboarding/organization_detail/$", views.org_detail_survey, name="org_detail_survey"),  # signup step 4
    url(r"^onboarding/delete_account/$", views.delete_my_account, name="delete_my_account"),  # signup step 4
    url(r"^onboarding/admin_activate/(?P<activation_key>[^/]*)$", views.admin_activation, name="admin_activation"),
    url(r"^onboarding/organizations/(?P<org_id>[0-9]+)/partner-networks/?$", views.get_partner_networks,
        name="organization_partner_networks")
]
