from django.conf import settings
from django.conf.urls import url

from .views import competency_assessments_score_view, record_competency_assessment


urlpatterns = [
    url(r'^api/courses/{}/courseware/(?P<chapter_id>[^/]*)/(?P<section_id>[^/]*)/(?P<is_pre>(True|False))/competency_assessments_score/$'.
        format(settings.COURSE_ID_PATTERN), competency_assessments_score_view,
        name='competency_assessments_score'),
    url(r'^api/record_competency_assessment/$', record_competency_assessment, name='record_competency_assessment')
]
