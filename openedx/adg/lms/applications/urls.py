"""
All urls for applications app
"""
from django.urls import path
from django.views.generic import TemplateView

from openedx.adg.lms.applications.views import ContactInformationView

urlpatterns = [
    path('', TemplateView.as_view(template_name='adg/lms/applications/hub.html'), name='application_hub'),
    path('contact', ContactInformationView.as_view(), name='application_contact'),
    path('experience', TemplateView.as_view(template_name='adg/lms/applications/experience.html'),
         name='application_experience'),
    path('cover_letter', TemplateView.as_view(template_name='adg/lms/applications/cover_letter.html'),
         name='application_cover_letter'),
    path('success', TemplateView.as_view(template_name='adg/lms/applications/success.html'),
         name='application_success'),
]
