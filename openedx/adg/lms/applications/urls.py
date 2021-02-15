"""
All urls for applications app
"""
from django.urls import path

from .views import (
    ApplicationHubView,
    ApplicationSuccessView,
    ContactInformationView,
    CoverLetterView,
    EducationAndExperienceView
)

urlpatterns = [
    path('', ApplicationHubView.as_view(), name='application_hub'),
    path('contact', ContactInformationView.as_view(), name='application_contact'),
    path('education_experience', EducationAndExperienceView.as_view(), name='application_education_experience'),
    path('cover_letter', CoverLetterView.as_view(), name='application_cover_letter'),
    path('success', ApplicationSuccessView.as_view(), name='application_success'),
]
