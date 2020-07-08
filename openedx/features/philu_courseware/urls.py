from django.conf import settings
from django.conf.urls import url

from .views import competency_assessments_score_view, record_and_fetch_competency_assessment


urlpatterns = [
    url(r'^api/courses/courseware/(?P<chapter_id>[^/]*)/competency_assessments_score/$',
        competency_assessments_score_view, name='competency_assessments_score'),
    url(r'^api/record_and_fetch_competency_assessment/(?P<chapter_id>[a-z0-9]+)/$', record_and_fetch_competency_assessment, name='record_and_fetch_competency_assessment')
]
