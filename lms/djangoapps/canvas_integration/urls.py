"""
Remote Gradebook API endpoint urls.
"""

from django.conf.urls import url

from canvas_integration import views

urlpatterns = [
    url(r'^add_enrollments_using_canvas$',
        views.add_enrollments_using_canvas, name="add_enrollments_using_canvas"),
]
