"""
URLs for save_for_later v1
"""


from django.conf.urls import url

from lms.djangoapps.save_for_later.api.v1.views import SaveForLaterApiView

urlpatterns = [
    url(r'^save/course/', SaveForLaterApiView.as_view(), name='save_course'),
]
