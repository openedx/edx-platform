"""
Branding API endpoint urls.
"""

from lms.djangoapps.branding.views import footer
from django.urls import path

urlpatterns = [
    path('footer', footer, name="branding_footer"),
]
