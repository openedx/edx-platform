"""
Taxonomies API v1 URLs.
"""

from rest_framework.routers import DefaultRouter

from django.urls.conf import path, include

from openedx_tagging.core.tagging.rest_api.v1 import views as oel_tagging_views

from . import views

router = DefaultRouter()
router.register("taxonomies", views.TaxonomyOrgView, basename="taxonomy")
router.register("object_tags", oel_tagging_views.ObjectTagView, basename="object_tag")

urlpatterns = [
    path('', include(router.urls))
]
