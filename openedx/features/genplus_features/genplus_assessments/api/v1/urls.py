"""
URLs for genplus badges API v1.
"""
from django.conf.urls import url

from .views import (
    StudentAnswersView, ClassFilterViewSet, SkillAssessmentView
)

app_name = 'genplus_assessments_api_v1'

urlpatterns = [
    url(r'^students-response/(?P<class_id>\w+)/$', StudentAnswersView.as_view({'get': 'students_problem_response'}), name='students-response-view'),
    url(r'^aggregate-assessment-responses/(?P<class_id>\w+)/$', SkillAssessmentView.as_view({'get': 'aggregate_assessments_response'}), name='aggregate-assessment-responses-view'),
    url(r'^assessment-response/(?P<class_id>\w+)/$', SkillAssessmentView.as_view({'get': 'single_assessment_response'}), name='assessment-response-view'),
    url(r'^genz-filters/(?P<class_id>\w+)/$', ClassFilterViewSet.as_view())
]
