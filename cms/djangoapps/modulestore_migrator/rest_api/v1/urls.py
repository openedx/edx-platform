"""
Course to Library Import API v1 URLs.
"""
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import MigrationViewSet, BulkMigrationViewSet, MigrationInfoViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'migrations', MigrationViewSet, basename='migrations')
ROUTER.register(r'bulk_migration', BulkMigrationViewSet, basename='bulk-migration')

urlpatterns = [
    path('', include(ROUTER.urls)),
    path('migration_info/', MigrationInfoViewSet.as_view(), name='migration-info'),
]
