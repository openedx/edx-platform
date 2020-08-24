""" Verification API v1 views. """

from django.contrib.auth import get_user_model
from django.http import Http404
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView

from lms.djangoapps.verify_student.models import ManualVerification, SoftwareSecurePhotoVerification, SSOVerification
from lms.djangoapps.verify_student.services import IDVerificationService
from lms.djangoapps.verify_student.utils import most_recent_verification
from openedx.core.djangoapps.user_api.serializers import (
    IDVerificationDetailsSerializer,
    ManualVerificationSerializer,
    SoftwareSecurePhotoVerificationSerializer,
    SSOVerificationSerializer
)
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaffOrOwner


class IDVerificationStatusView(RetrieveAPIView):
    """ IDVerificationStatus detail endpoint. """
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsStaffOrOwner,)

    def get_serializer(self, *args, **kwargs):
        """
        Overrides default get_serializer in order to choose the correct serializer for the instance.
        """
        instance = args[0]
        kwargs['context'] = self.get_serializer_context()
        if isinstance(instance, SoftwareSecurePhotoVerification):
            return SoftwareSecurePhotoVerificationSerializer(*args, **kwargs)
        elif isinstance(instance, SSOVerification):
            return SSOVerificationSerializer(*args, **kwargs)
        else:
            return ManualVerificationSerializer(*args, **kwargs)

    def get_object(self):
        username = self.kwargs['username']
        photo_verifications = SoftwareSecurePhotoVerification.objects.filter(
            user__username=username).order_by('-updated_at')
        sso_verifications = SSOVerification.objects.filter(user__username=username).order_by('-updated_at')
        manual_verifications = ManualVerification.objects.filter(user__username=username).order_by('-updated_at')

        if photo_verifications or sso_verifications or manual_verifications:
            verification = most_recent_verification(
                photo_verifications,
                sso_verifications,
                manual_verifications,
                'updated_at'
            )
            self.check_object_permissions(self.request, verification)
            return verification

        raise Http404


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
            raise Http404
