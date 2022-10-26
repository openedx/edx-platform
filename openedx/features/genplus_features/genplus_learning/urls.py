"""
URLs for genplus learning app.
"""
from django.conf import settings
from django.conf.urls import url, include

from .views import update_lessons_structure


app_name = 'genplus_learning'

urlpatterns = (
     url(
        r'^course/{}/update_lessons?$'.format(
            settings.COURSE_KEY_PATTERN
        ),
        update_lessons_structure,
        name='update_lessons_structure',
    ),
    url(
        r'^api/v1/',
        include(
            'openedx.features.genplus_features.genplus_learning.api.v1.urls',
            namespace='genplus_learning_api_v1'
        )
    ),
)
