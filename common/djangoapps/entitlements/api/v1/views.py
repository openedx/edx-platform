import logging

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets
from rest_framework.response import Response

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

        if self.request.method in permissions.SAFE_METHODS:
            if (user.is_staff and
                    (self.request.query_params.get('user', None) is not None or
                     self.kwargs.get('uuid', None) is not None)):
                # Return the full query set so that the Filters class can be used to apply,
                # - The UUID Filter
                # - The User Filter to the GET request
                return CourseEntitlement.objects.all().select_related('user').select_related('enrollment_course_run')
            # Non Staff Users will only be able to retrieve their own entitlements
            return CourseEntitlement.objects.filter(user=user).select_related('user').select_related(
                'enrollment_course_run'
            )
        # All other methods require the full Query set and the Permissions class already restricts access to them
        # to Admin users
        return CourseEntitlement.objects.all().select_related('user').select_related('enrollment_course_run')

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to expire a record that is past the
        policy and is requested via the API before returning that record.
        """
        entitlement = self.get_object()
        entitlement.update_expired_at()
        serializer = self.get_serializer(entitlement)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """
        Override the list method to expire records that are past the
        policy and requested via the API before returning those records.
        """
        queryset = self.filter_queryset(self.get_queryset())
        user = self.request.user
        if not user.is_staff:
            with transaction.atomic():
                for entitlement in queryset:
                    entitlement.update_expired_at()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
