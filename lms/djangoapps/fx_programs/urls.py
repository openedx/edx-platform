from .views import index, add_course
from django.urls import path

urlpatterns = [
    path('', index, name='index'),
    path('add_course', add_course, name='add_course'),
]