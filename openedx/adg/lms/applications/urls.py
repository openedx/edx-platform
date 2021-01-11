"""
All urls for applications app
"""
from django.urls import path
from django.views.generic import TemplateView

from .views import ApplicationHubView, ApplicationSuccessView, ContactInformationView, CoverLetterView

urlpatterns = [
    path('', ApplicationHubView.as_view(), name='application_hub'),
    path('contact', ContactInformationView.as_view(), name='application_contact'),
    path('experience', TemplateView.as_view(template_name='adg/lms/applications/experience.html'),
         name='application_experience'),
    path('cover_letter', CoverLetterView.as_view(), name='application_cover_letter'),
    path('success', ApplicationSuccessView.as_view(), name='application_success'),
]
