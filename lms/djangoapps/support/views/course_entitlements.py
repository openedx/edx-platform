"""
Support tool for changing and granting course entitlements
"""
from django.contrib.auth.models import User
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from edxmako.shortcuts import render_to_response
from entitlements.api.v1.permissions import IsAdminOrAuthenticatedReadOnly
from entitlements.api.v1.serializers import SupportCourseEntitlementSerializer
from entitlements.models import CourseEntitlement, CourseEntitlementSupportDetail
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.support.decorators import require_support_permission
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf

REQUIRED_CREATION_FIELDS = ['course_uuid', 'reason', 'mode']


class EntitlementSupportView(View):
    """
    View for viewing and changing learner enrollments, used by the
    support team.
    """
    @method_decorator(require_support_permission)
    def get(self, request):
        """Render the enrollment support tool view."""
        support_actions = CourseEntitlementSupportDetail.get_support_actions_list()

        ecommerce_url = EcommerceService().get_order_dashboard_url()
        context = {
            'username': request.GET.get('user', ''),
            'uses_bootstrap': True,
            'ecommerce_url': ecommerce_url,
            'support_actions': support_actions
        }
        return render_to_response('support/entitlement.html', context)


class EntitlementSupportListView(viewsets.ModelViewSet):
    """
    Allows viewing and changing learner course entitlements, used the support team.
    """
    authentication_classes = (JwtAuthentication, SessionAuthenticationCrossDomainCsrf,)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrAuthenticatedReadOnly,)
    queryset = CourseEntitlement.objects.all()
    serializer_class = SupportCourseEntitlementSerializer

    @method_decorator(require_support_permission)
    def list(self, request, username_or_email):  # pylint: disable=unused-argument
        """
        Returns a list of course entitlements for the given user, along with details of any
        support team interactions with each of the course entitlements.
        """
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return Response([])

        return Response(self.serializer_class(self.queryset.filter(user=user), many=True).data)

    @method_decorator(require_support_permission)
    def update(self, request, username_or_email):  # pylint: disable=unused-argument
        """ Allows support staff to update an existing course entitlement. """
        support_user = request.user
        entitlement_uuid = request.data.get('entitlement_uuid')
        if not entitlement_uuid:
            return HttpResponseBadRequest(u'The field {fieldname} is required.'.format(fieldname='entitlement_uuid'))
        reason = request.data.get('reason')
        if not reason:
            return HttpResponseBadRequest(u'The field {fieldname} is required.'.format(fieldname='reason'))
        comments = request.data.get('comments', None)
        try:
            entitlement = CourseEntitlement.objects.get(uuid=entitlement_uuid)
        except CourseEntitlement.DoesNotExist:
            return HttpResponseBadRequest(
                u'Could not find entitlement {entitlement_uuid} for update'.format(
                    entitlement_uuid=entitlement_uuid
                )
            )
        if reason == CourseEntitlementSupportDetail.LEAVE_SESSION:
            return self._reinstate_entitlement(support_user, entitlement, comments)

    def _reinstate_entitlement(self, support_user, entitlement, comments):
        """ Allows support staff to unexpire a user's entitlement."""
        if entitlement.enrollment_course_run is None:
            return HttpResponseBadRequest(
                u"Entitlement {entitlement} has not been spent on a course run.".format(
                    entitlement=entitlement
                )
            )
        try:
            with transaction.atomic():
                unenrolled_run = entitlement.reinstate()
                CourseEntitlementSupportDetail.objects.create(
                    entitlement=entitlement, reason=CourseEntitlementSupportDetail.LEAVE_SESSION, comments=comments,
                    unenrolled_run=unenrolled_run, support_user=support_user
                )
            return Response(
                data=SupportCourseEntitlementSerializer(instance=entitlement).data
            )
        except DatabaseError:
            return HttpResponseBadRequest(
                u'Failed to reinstate entitlement {entitlement}'.format(entitlement=entitlement))

    @method_decorator(require_support_permission)
    def create(self, request, username_or_email):  # pylint: disable=arguments-differ
        """ Allows support staff to grant a user a new entitlement for a course. """
        support_user = request.user
        comments = request.data.get('comments', None)

        creation_fields = {}
        missing_fields_string = ''
        for field in REQUIRED_CREATION_FIELDS:
            creation_fields[field] = request.data.get(field)
            if not creation_fields.get(field):
                missing_fields_string = missing_fields_string + ' ' + field
        if missing_fields_string:
            return HttpResponseBadRequest(
                u'The following required fields are missing from the request:{missing_fields}'.format(
                    missing_fields=missing_fields_string
                )
            )

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return HttpResponseBadRequest(
                u'Could not find user {username_or_email}.'.format(
                    username_or_email=username_or_email,
                )
            )

        entitlement = CourseEntitlement.objects.create(
            user=user, course_uuid=creation_fields['course_uuid'], mode=creation_fields['mode']
        )
        CourseEntitlementSupportDetail.objects.create(
            entitlement=entitlement, reason=creation_fields['reason'], comments=comments, support_user=support_user
        )
        return Response(
            status=status.HTTP_201_CREATED,
            data=SupportCourseEntitlementSerializer(instance=entitlement).data
        )
