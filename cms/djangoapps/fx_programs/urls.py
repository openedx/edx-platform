from .views import index
from django.urls import path
from .api import FxProgramsAPI

urlpatterns = [
    path('', index, name='index'),
    path('api/programs', FxProgramsAPI.as_view(), name='programs'),
]