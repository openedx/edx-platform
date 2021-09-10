"""
Urls for the django_comment_client.
"""


from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('', include('lms.djangoapps.discussion.django_comment_client.base.urls')),
]
