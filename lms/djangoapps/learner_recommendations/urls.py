"""
Learner Recommendations URL routing configuration.
"""

from django.conf import settings
from django.urls import re_path

from lms.djangoapps.learner_recommendations import views

app_name = "learner_recommendations"

urlpatterns = [
    re_path(fr'^algolia/courses/{settings.COURSE_ID_PATTERN}/$',
            views.AlgoliaCoursesSearchView.as_view(),
            name='algolia_courses'),
]
