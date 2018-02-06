"""
Support tool for changing and granting course entitlements
"""
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets
from six import text_type

from edxmako.shortcuts import render_to_response
from entitlements.api.v1.permissions import IsAdminOrAuthenticatedReadOnly
from entitlements.api.v1.serializers import SupportCourseEntitlementSerializer
from entitlements.models import CourseEntitlement, CourseEntitlementSupportDetail
from lms.djangoapps.support.decorators import require_support_permission
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from util.json_request import JsonResponse

log = logging.getLogger(__name__)


class EntitlementSupportView(viewsets.ModelViewSet):
    """
    Allows viewing and changing learner course entitlements, used the support team.
    """
    authentication_classes = (JwtAuthentication, SessionAuthenticationCrossDomainCsrf,)
    permission_classes = (permissions.IsAuthenticated, IsAdminOrAuthenticatedReadOnly,)
    serializer_class = SupportCourseEntitlementSerializer

    def get_queryset(self):
        """
        Returns a list of entitlements for the given user, along with
        information about previous manual entitlements changes.
        """
        username_or_email = self.request.user
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return HttpResponseBadRequest(
                u'Could not find user {username}.'.format(
                    username=username_or_email,
                )
            )

        return CourseEntitlement.objects.filter(user=user).order_by('created')

    def put(self, request, username_or_email):
        """ Allows support staff to unexpire a user's entitlement."""
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            course_uuid = request.data['course_uuid']
            reason = request.data['reason']
            entitlement = get_most_recent_entitlement(user=user, course_uuid=course_uuid)
        except KeyError as err:
            return HttpResponseBadRequest(u'The field {} is required.'.format(text_type(err)))
        except User.DoesNotExist:
            return HttpResponseBadRequest(
                u'Could not find user {username}.'.format(
                    username=username_or_email,
                )
            )
        if entitlement:
            if entitlement.expired_at == None:
                return HttpResponseBadRequest(
                    u"Entitlement for user {user} to course {course} is not expired.".format(
                        user=entitlement.user.username,
                        course=entitlement.course_uuid
                    )
                )
            if entitlement.enrollment_course_run == None:
                return HttpResponseBadRequest(
                    u"Entitlement for user {user} to course {course} has not been spent on a course run.".format(
                        user=entitlement.user.username,
                        course=entitlement.course_uuid
                    )
                )
            unenrolled_run = self.unexpire_entitlement(entitlement)
            CourseEntitlementSupportDetail.objects.create(
                entitlement=entitlement, reason=reason, comments=comments, unenrolled_run=unenrolled_run
            )
            return JsonResponse(SupportCourseEntitlementSerializer(instance=entitlement).data)
        else:
            return HttpResponseBadRequest(
                u'Could not find an entitlement for user {username} in course {course}'.format(
                    username=username_or_email,
                    course=course_uuid
                )
            )
    
    def post(self, request, username_or_email):
        """ Allows support staff to grant a user a new entitlement for a course. """
        username_or_email = self.request.user
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            course_uuid = request.data['course_uuid']
            reason = request.data['reason']
            mode = request.data['mode']
        except KeyError as err:
            return HttpResponseBadRequest(u'The field {} is required.'.format(text_type(err)))
        except User.DoesNotExist:
            return HttpResponseBadRequest(
                u'Could not find user {username}.'.format(
                    username=username_or_email,
                )
            )
        if CourseEntitlement.get_entitlement_if_active(user, course_uuid) is not None:
            return HttpResponseBadRequest(u'User {user} has an active entitlement in course {course}'.foramt(
                user=username_or_email, course=course_uuid
            ))
        else:
            entitlement = CourseEntitlement.objects.create(user=user, course_uuid=course_uuid, mode=mode)
            CourseEntitlementSupportDetail.objects.create(entitlement=entitlement, reason=reason, comments=comments)
            return JsonResponse(SupportCourseEntitlementSerializer(instance=entitlement).data)

    @staticmethod
    def get_most_recent_entitlement(user, course_uuid):
        """
        Returns the most recently created entitlement for the given user in the given course.
        
        Args: 
            user (User): user object record for which we are retrieving the entitlement.
            course_uuid (UUID): identified of the course for which we are retrieving the learner's entitlement.
        """
        return CourseEntitlement.objects.filter(user=user, course_uuid=course_uuid).latest('created')

    @staticmethod
    def unexpire_entitlement(entitlement):
        """
        Unenrolls a user from the run on which they have spent the given entitlement and
        sets the entitlement's expired_at date to null.
        """
        unenrolled_run = entitlement.enrollment_course_run
        entitlement.expired_at = None
        entitlement.enrollment_course_run.deactivate()
        entitlement.enrollment_course_run = None
        entitlement.save()
        return unenrolled_run
