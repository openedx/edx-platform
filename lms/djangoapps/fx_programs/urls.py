from .views import FxProgramsView
from django.urls import path

urlpatterns = [
    path('fx_programs', FxProgramsView.as_view(), name='index'),
]