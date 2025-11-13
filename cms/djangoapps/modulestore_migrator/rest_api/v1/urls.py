"""
Course to Library Import API v1 URLs.
"""

from rest_framework.routers import SimpleRouter

from .views import BulkMigrationViewSet, LibraryCourseMigrationViewSet, MigrationViewSet

ROUTER = SimpleRouter()
ROUTER.register(r'migrations', MigrationViewSet, basename='migrations')
ROUTER.register(r'bulk_migration', BulkMigrationViewSet, basename='bulk-migration')
ROUTER.register(
    r'library/(?P<lib_key_str>[^/.]+)/migrations/courses',
    LibraryCourseMigrationViewSet,
    basename='library-migrations',
)


urlpatterns = ROUTER.urls
