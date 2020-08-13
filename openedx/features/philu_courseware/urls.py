from django.conf import settings
from django.conf.urls import url

from .views import CompetencyAssessmentAPIView, RevertPostAssessmentAttemptsAPIView

urlpatterns = [
    url(r'^api/competency_assessment/(?P<chapter_id>[a-z0-9]+)/$',
        CompetencyAssessmentAPIView.as_view(), name='competency_assessment'),
    url(r'^api/courses/{course_id}/courseware/revert_user_post_assessment_attempts/$'.format(
        course_id=settings.COURSE_ID_PATTERN), RevertPostAssessmentAttemptsAPIView.as_view(),
        name='revert_user_post_assessment_attempts')
]
