from rest_framework import routers

from openedx.features.edly.api.v1.views.course_enrollments import EdlyCourseEnrollmentViewSet
from openedx.features.edly.api.v1.views.user_sites import UserSitesViewSet

router = routers.SimpleRouter()
router.register(r'user_sites', UserSitesViewSet, base_name='user_sites')
router.register(
    r'course_enrollment',
    EdlyCourseEnrollmentViewSet,
    base_name='course_enrollment',
    )

urlpatterns = router.urls
