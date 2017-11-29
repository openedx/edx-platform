import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets

from entitlements.api.v1.filters import CourseEntitlementFilter
from entitlements.api.v1.permissions import IsAdminOrAuthenticatedReadOnly
from entitlements.api.v1.serializers import CourseEntitlementSerializer
from entitlements.models import CourseEntitlement
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class EntitlementViewSet(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthenticationCrossDomainCsrf,)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrAuthenticatedReadOnly,)
    lookup_value_regex = '[0-9a-f-]+'
    lookup_field = 'uuid'
    serializer_class = CourseEntitlementSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CourseEntitlementFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CourseEntitlement.objects.all().select_related('user')
        return CourseEntitlement.objects.filter(user=user).select_related('user')

    def perform_destroy(self, instance):
        """
        This method is an override and is called by the DELETE method
        """
        save_model = False
        if instance.expired_at is None:
            instance.expired_at = timezone.now()
            log.info('Set expired_at to [%s] for course entitlement [%s]', instance.expired_at, instance.uuid)
            save_model = True

        if instance.enrollment_course_run is not None:
            CourseEnrollment.unenroll(
                user=instance.user,
                course_id=instance.enrollment_course_run.course_id,
                skip_refund=True
            )
            enrollment = instance.enrollment_course_run
            instance.enrollment_course_run = None
            save_model = True
            log.info(
                'Unenrolled user [%s] from course run [%s] as part of revocation of course entitlement [%s]',
                instance.user.username,
                enrollment.course_id,
                instance.uuid
            )
        if save_model:
            instance.save()
