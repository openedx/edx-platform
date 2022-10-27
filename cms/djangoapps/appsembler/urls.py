"""Perform Studio local login/logout

The purpose of this is to address the issue that Ironwood introduced login
redirect to the LMS, which breaks in multisite custom domain environments

We have this code in the Appsembler CMS app to help isolate custom code
"""
from django.urls import path
from .views import LoginView, StudioLogoutView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', StudioLogoutView.as_view(), name='logout'),
]
