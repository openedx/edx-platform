"""
Urls for the django_comment_client.
"""


from django.urls import include, path

urlpatterns = [
    path('', include('lms.djangoapps.discussion.django_comment_client.base.urls')),
]
