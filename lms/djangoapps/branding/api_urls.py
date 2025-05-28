"""
Branding API endpoint urls.
"""


from django.urls import path

from lms.djangoapps.branding.views import footer, IndexPageConfigView

urlpatterns = [
    path('footer', footer, name="branding_footer"),
    path('index', IndexPageConfigView.as_view(), name="index_page_config"),
]
