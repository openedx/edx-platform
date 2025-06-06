"""
Branding API endpoint urls.
"""


from django.urls import path, re_path

from lms.djangoapps.branding.views import footer, WaffleFlagsView
from openedx.core.constants import COURSE_ID_PATTERN

urlpatterns = [
    path('footer', footer, name="branding_footer"),
    re_path(fr'^waffle-flags(?:/{COURSE_ID_PATTERN})?$', WaffleFlagsView.as_view(), name="branding_waffle_flags"),
]
