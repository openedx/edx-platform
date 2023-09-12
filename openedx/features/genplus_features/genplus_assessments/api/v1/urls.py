"""
URLs for genplus badges API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    StudentAnswersViewSet, ClassFilterApiView, SkillAssessmentViewSet, SkillAssessmentAdminViewSet,
    SaveRatingResponseApiView, SkillReflectionApiView, SkillReflectionIndividualApiView,
    SkillReflectionQuestionModelView
)

# TODO: remove this ClassFilterApiView endpoint

app_name = 'genplus_assessments_api_v1'

router = DefaultRouter()
router.register('question', SkillReflectionQuestionModelView, basename='skill-reflection-question')

urlpatterns = [
    url(r'^students-response/(?P<class_id>\w+)/$', StudentAnswersViewSet.as_view(
        {'get': 'students_problem_response'}), name='students-response-view'),
    url(r'^aggregate-assessment-responses/(?P<class_id>\w+)/$', SkillAssessmentViewSet.as_view(
        {'get': 'aggregate_assessments_response'}), name='aggregate-assessment-responses-view'),
    url(r'^assessment-response/(?P<class_id>\w+)/$', SkillAssessmentViewSet.as_view(
        {'get': 'single_assessment_response'}), name='assessment-response-view'),
    url(r'^genz-filters/(?P<class_id>\w+)/$', ClassFilterApiView.as_view()),
    url(r'^program-mapping/(?P<program_slug>\w+)/$', SkillAssessmentAdminViewSet.as_view({
        'get': 'get_skills_assessment_question_mapping',
        'post': 'update_skills_assessment_question_mapping'
    }), name='skills-assessment-question-mapping'),
    url(r'^save-rating-response/$', SaveRatingResponseApiView.as_view()),
    url(r'skill-reflection/(?P<class_id>\d+)/$', SkillReflectionApiView.as_view()),
    url(r'skill-reflection-individual/(?P<user_id>\d+)/$', SkillReflectionIndividualApiView.as_view()),
    path('skill-reflection/', include(router.urls)),
]
