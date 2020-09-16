from django.conf import settings
from django.conf.urls import url

from .views import course_custom_settings

urlpatterns = [
    url(r'^settings/custom/{}$'.format(settings.COURSE_KEY_PATTERN), course_custom_settings, name='custom_settings'),
]
