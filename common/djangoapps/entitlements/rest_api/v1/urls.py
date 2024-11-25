"""
URLs for the V1 of the Entitlements API.
"""

from django.urls import include
from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

<<<<<<< HEAD
from .views import EntitlementEnrollmentViewSet, EntitlementViewSet, SubscriptionsRevokeVerifiedAccessView
=======
from .views import EntitlementEnrollmentViewSet, EntitlementViewSet
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

router = DefaultRouter()
router.register(r'entitlements', EntitlementViewSet, basename='entitlements')

ENROLLMENTS_VIEW = EntitlementEnrollmentViewSet.as_view({
    'post': 'create',
    'delete': 'destroy',
})

app_name = 'v1'
urlpatterns = [
    path('', include(router.urls)),
    re_path(
        fr'entitlements/(?P<uuid>{EntitlementViewSet.ENTITLEMENT_UUID4_REGEX})/enrollments$',
        ENROLLMENTS_VIEW,
        name='enrollments'
    ),
<<<<<<< HEAD
    path(
        'subscriptions/entitlements/revoke',
        SubscriptionsRevokeVerifiedAccessView.as_view(),
        name='revoke_subscriptions_verified_access'
    )
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
]
