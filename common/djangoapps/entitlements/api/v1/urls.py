from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import EntitlementViewSet, EntitlementEnrollmentViewSet

router = DefaultRouter()
router.register(r'entitlements', EntitlementViewSet, base_name='entitlements')

enrollments_view = EntitlementEnrollmentViewSet.as_view({
    'post': 'create',
    'delete': 'destroy',
})


urlpatterns = [
    url(r'', include(router.urls)),
    url(
        r'entitlements/(?P<uuid>[0-9a-f-]+)/enrollments/$',
        enrollments_view,
        name='enrollments'
    )
]
