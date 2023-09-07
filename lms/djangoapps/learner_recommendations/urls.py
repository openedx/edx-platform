"""
Learner Recommendations URL routing configuration.
"""

from django.conf import settings
from django.urls import path
from django.urls import re_path

from lms.djangoapps.learner_recommendations import views

app_name = "learner_recommendations"

urlpatterns = [
    re_path(fr'^amplitude/{settings.COURSE_ID_PATTERN}/$',
            views.AboutPageRecommendationsView.as_view(),
            name='amplitude_recommendations'),
    re_path(fr'^cross_product/{settings.COURSE_ID_PATTERN}/$',
            views.CrossProductRecommendationsView.as_view(),
            name='cross_product_recommendations'),
    path('product_recommendations/',
         views.ProductRecommendationsView.as_view(),
         name='product_recommendations_amplitude_only'),
    re_path(fr'^product_recommendations/{settings.COURSE_ID_PATTERN}/$',
            views.ProductRecommendationsView.as_view(),
            name='product_recommendations'),
    path("courses/",
         views.DashboardRecommendationsApiView.as_view(),
         name="courses"),
    path('recommendations_context/',
         views.RecommendationsContextView.as_view(),
         name='recommendations_context'),
]
