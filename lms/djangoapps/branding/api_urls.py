"""
Branding API endpoint urls.
"""


from django.conf.urls import url

from lms.djangoapps.branding.views import footer

urlpatterns = [
    url(r"^footer$", footer, name="branding_footer"),
]
