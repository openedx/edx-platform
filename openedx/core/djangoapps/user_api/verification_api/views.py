""" Verification API v1 views. """
from django.http import Http404
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import RetrieveAPIView
from rest_framework_oauth.authentication import OAuth2Authentication

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSOVerification, ManualVerification
from lms.djangoapps.verify_student.utils import most_recent_verification
from openedx.core.djangoapps.user_api.serializers import (
    SoftwareSecurePhotoVerificationSerializer, SSOVerificationSerializer, ManualVerificationSerializer,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner


class IDVerificationStatusView(RetrieveAPIView):
    """ IDVerificationStatus detail endpoint. """
    authentication_classes = (JwtAuthentication, OAuth2Authentication, SessionAuthentication,)
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
