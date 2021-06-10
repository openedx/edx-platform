"""
All urls for applications app
"""
from django.urls import path

from .views import (
    ApplicationHubView,
    ApplicationIntroductionView,
    BusinessLineInterestView,
    ContactInformationView,
    EducationAndExperienceView
)

urlpatterns = [
    path('', ApplicationIntroductionView.as_view(), name='application_introduction'),
    path('progress', ApplicationHubView.as_view(), name='application_hub'),
    path('contact', ContactInformationView.as_view(), name='application_contact'),
    path('education_experience', EducationAndExperienceView.as_view(), name='application_education_experience'),
    path('business_line', BusinessLineInterestView.as_view(), name='application_business_line_interest'),
]
