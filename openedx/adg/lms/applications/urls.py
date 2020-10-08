"""
All urls for applications app
"""
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='adg/lms/applications/hub.html'), name='application_hub'),
    path('contact', TemplateView.as_view(template_name='adg/lms/applications/contact-info.html'),
        name='application_contact'),
    path('experience', TemplateView.as_view(template_name='adg/lms/applications/experience.html'),
        name='application_experience'),
    path('cover_letter', TemplateView.as_view(template_name='adg/lms/applications/cover_letter.html'),
        name='application_cover_letter'),
    path('success', TemplateView.as_view(template_name='adg/lms/applications/success.html'),
        name='application_success'),
]
