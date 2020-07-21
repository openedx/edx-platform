from django.conf import settings
from django.conf.urls import url

from .views import (
    competency_assessments_score_view,
    record_and_fetch_competency_assessment,
    revert_user_post_assessment_attempts
)

urlpatterns = [
    url(r'^api/courses/courseware/(?P<chapter_id>[^/]*)/competency_assessments_score/$',
        competency_assessments_score_view, name='competency_assessments_score'),
    url(r'^api/record_and_fetch_competency_assessment/(?P<chapter_id>[a-z0-9]+)/$',
        record_and_fetch_competency_assessment, name='record_and_fetch_competency_assessment'),
    url(r'^api/courses/{course_id}/courseware/revert_user_post_assessment_attempts/$'.format(
        course_id=settings.COURSE_ID_PATTERN), revert_user_post_assessment_attempts,
        name='revert_user_post_assessment_attempts')
]
