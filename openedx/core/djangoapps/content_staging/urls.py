"""
Studio URL configuration for Content Staging (& Clipboard)
"""
from django.urls import path, include

from . import views

urlpatterns = [
    path('api/content-staging/v1/', include([
        path('clipboard/', views.ClipboardEndpoint.as_view()),
    ])),
]
