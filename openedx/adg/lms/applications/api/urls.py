"""
All urls for applications APIs
"""
from rest_framework.routers import DefaultRouter

from .views import EducationViewSet, ReferenceViewSet, WorkExperienceViewSet

router = DefaultRouter()
router.register('education', EducationViewSet, basename='education')
router.register('work_experience', WorkExperienceViewSet, basename='work_experience')
router.register('reference', ReferenceViewSet, basename='reference')

app_name = 'applications'

urlpatterns = router.urls
