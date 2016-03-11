"""
Learner's Dashboard urls
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^programs/$', views.view_programs, name='program_listing_view'),
]
