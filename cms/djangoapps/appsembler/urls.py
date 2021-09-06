"""Perform Studio local login/logout

The purpose of this is to address the issue that Ironwood introduced login
redirect to the LMS, which breaks in multisite custom domain environments

We have this code in the Appsembler CMS app to help isolate custom code
"""
from django.conf import settings
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import LoginView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(
         next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
]
