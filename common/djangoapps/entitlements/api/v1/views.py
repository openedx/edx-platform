import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from openedx.core.djangoapps.catalog.utils import get_course_runs_for_course
from entitlements.api.v1.filters import CourseEntitlementFilter
from entitlements.api.v1.permissions import IsAdminOrAuthenticatedReadOnly
from entitlements.models import CourseEntitlement
from entitlements.api.v1.serializers import CourseEntitlementSerializer
from entitlements.models import CourseEntitlement
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from opaque_keys.edx.keys import CourseKey

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


class EntitlementEnrollmentViewSet(viewsets.GenericViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = CourseEntitlement.objects.all()
    serializer_class = CourseEntitlementSerializer

    def _enroll_entitlement(self, entitlement, course_session_key, user):
        enrollment = CourseEnrollment.enroll(
            user=user,
            course_key=course_session_key,
            mode=entitlement.mode,
        )

        CourseEntitlement.set_enrollment(entitlement, enrollment)

    def _unenroll_entitlement(self, entitlement, course_session_key, user):
        CourseEnrollment.unenroll(user, course_session_key, skip_refund=True)
        CourseEntitlement.set_enrollment(entitlement, None)

    def create(self, request, uuid):
        course_session_id = request.data.get('course_run_id', None)

        if not course_session_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Course Run ID was not provided."
            )

        # Verify that the user has an Entitlement for the provided Course UUID.
        try:
            entitlement = CourseEntitlement.objects.get(uuid=uuid, user=request.user, expired_at=None)
        except CourseEntitlement.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Entitlement for this UUID does not exist or is Expired."
            )

        # Verify the course run ID is of the same type as the Course entitlement.
        course_run_valid = False
        course_runs = get_course_runs_for_course(entitlement.course_uuid)
        for run in course_runs:
            if course_session_id == run.get('key', ''):
                course_run_valid = True

        if not course_run_valid:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Course Run ID is not a match for this Course Entitlement."
            )

        # Determine if this is a Switch session or a simple enroll and handle both.
        if entitlement.enrollment_course_run is None:
            self._enroll_entitlement(
                entitlement=entitlement,
                course_session_key=CourseKey.from_string(course_session_id),
                user=request.user
            )
        else:
            if entitlement.enrollment_course_run.course_id != course_session_id:
                self._unenroll_entitlement(
                    entitlement=entitlement,
                    course_session_key=entitlement.enrollment_course_run.course_id,
                    user=request.user
                )
                self._enroll_entitlement(
                    entitlement=entitlement,
                    course_session_key=CourseKey.from_string(course_session_id),
                    user=request.user
                )

        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'uuid': entitlement.uuid,
                'course_run_id': course_session_id,
                'is_active': True
            }
        )

    def destroy(self, request, uuid):
        """
        On DELETE call to this API we will unenroll the course enrollment for the provided uuid
        """
        try:
            entitlement = CourseEntitlement.objects.get(uuid=uuid, user=request.user, expired_at=None)
        except CourseEntitlement.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="The Entitlement for this UUID does not exist or is Expired."
            )

        if entitlement.enrollment_course_run is None:
            return Response()

        self._unenroll_entitlement(
            entitlement=entitlement,
            course_session_key=entitlement.enrollment_course_run.course_id,
            user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
