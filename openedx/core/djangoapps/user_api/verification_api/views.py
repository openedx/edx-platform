""" Verification API v1 views. """

from django.contrib.auth import get_user_model
from django.http import Http404
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
<<<<<<< HEAD
from edx_rest_framework_extensions.permissions import IsStaff
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.user_api.serializers import IDVerificationDetailsSerializer
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaffOrOwner


class IDVerificationStatusView(APIView):
    """ IDVerification Status endpoint """
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsStaffOrOwner,)

    def get(self, request, **kwargs):  # lint-amnesty, pylint: disable=missing-function-docstring
        username = kwargs.get('username')
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            user_status = IDVerificationService.user_status(user)
            if user_status.get('status') == 'none':
                raise Http404

            return Response({
                "is_verified": user_status.get('status') == 'approved',
                "status": user_status.get('status'),
                "expiration_datetime": user_status.get('verification_expiry', '')
            })

        except User.DoesNotExist:
            raise Http404  # lint-amnesty, pylint: disable=raise-missing-from


class IDVerificationStatusDetailsView(ListAPIView):
    """ IDVerificationStatusDeetails endpoint to retrieve more details about ID Verification status """
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsStaffOrOwner,)
    pagination_class = None  # No need for pagination for this yet

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return IDVerificationDetailsSerializer(*args, **kwargs)

    def get_queryset(self):
        username = self.kwargs['username']
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            verifications = IDVerificationService.verifications_for_user(user)
            if not verifications:
                raise Http404

            return sorted(verifications, key=lambda x: x.updated_at, reverse=True)
        except User.DoesNotExist:
            raise Http404  # lint-amnesty, pylint: disable=raise-missing-from
<<<<<<< HEAD


class IDVerificationSupportView(APIView):
    """ IDVerification endpoint for support-tool"""
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsStaff,)

    def get(self, request, **kwargs):
        """
        Get IDV attempt details by attempt_id. Only accessible by global staff.
        """
        attempt_id = kwargs.get('attempt_id')
        verification_detail = IDVerificationService.get_verification_details_by_id(attempt_id)
        if not verification_detail:
            raise Http404
        return Response(
            IDVerificationDetailsSerializer(verification_detail).data
        )
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
