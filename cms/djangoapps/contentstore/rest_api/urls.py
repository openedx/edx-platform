"""
Contentstore API URLs.
"""

from django.urls import path
from django.urls import include

from lms.djangoapps.experiments.routers import DefaultRouter
from .v0 import urls as v0_urls
from .v0.views.course_import_templates import CourseImportTemplateViewSet
from .v1 import urls as v1_urls
from .v2 import urls as v2_urls

app_name = 'cms.djangoapps.contentstore'


router = DefaultRouter()
router.register(r'course-import-templates', CourseImportTemplateViewSet, basename='course-import-templates')


urlpatterns = [
    path('v0/', include(v0_urls)),
    path('v0/', include(router.urls)),
    path('v1/', include(v1_urls)),
    path('v2/', include(v2_urls)),
]
