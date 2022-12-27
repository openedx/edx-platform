"""Learner home URL routing configuration"""

from django.urls import path

from lms.djangoapps.learner_home.twou_widgets import views

urlpatterns = [
    path(
        "",
        views.TwoUWidgetContextView.as_view(),
        name="twou_widget_context",
    ),
]
