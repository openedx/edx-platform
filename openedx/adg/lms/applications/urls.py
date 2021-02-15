"""
All urls for applications app
"""
from django.urls import path
from django.views.generic import TemplateView

from .views import ApplicationHubView, ApplicationSuccessView, ContactInformationView, EducationAndExperienceView

urlpatterns = [
    path('', ApplicationHubView.as_view(), name='application_hub'),
    path('contact', ContactInformationView.as_view(), name='application_contact'),
    path('education_experience', EducationAndExperienceView.as_view(), name='application_education_experience'),
    path('cover_letter', TemplateView.as_view(template_name='adg/lms/applications/cover_letter.html'),
         name='application_cover_letter'),
    path('success', ApplicationSuccessView.as_view(), name='application_success'),
]
