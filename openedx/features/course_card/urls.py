"""
The urls for on-boarding app.
"""
from django.conf.urls import url

from openedx.features.course_card import views

urlpatterns = [
    url(r"^course-cards/$", views.get_course_cards, name="get_course_cards"),
]
