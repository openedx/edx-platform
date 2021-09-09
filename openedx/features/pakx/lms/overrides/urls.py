from django.conf import settings
from django.conf.urls import url

from .views import overview_tab_view, business_view

urlpatterns = [
    url(
        r'^courses/{course_id}/overview/$'.format(course_id=settings.COURSE_ID_PATTERN),
        overview_tab_view,
        name='overview_tab_view'
    ),
    url(r'^business/$', business_view, name='home-business'),
]
