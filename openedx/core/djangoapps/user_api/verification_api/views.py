""" Verification API v1 views. """
from django.http import Http404
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import RetrieveAPIView
from rest_framework_oauth.authentication import OAuth2Authentication

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.user_api.serializers import SoftwareSecurePhotoVerificationSerializer
from openedx.core.lib.api.permissions import IsStaffOrOwner


class PhotoVerificationStatusView(RetrieveAPIView):
    """ PhotoVerificationStatus detail endpoint. """
    authentication_classes = (JwtAuthentication, OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsStaffOrOwner,)
    serializer_class = SoftwareSecurePhotoVerificationSerializer

    def get_object(self):
        username = self.kwargs['username']
        verifications = SoftwareSecurePhotoVerification.objects.filter(user__username=username).order_by('-updated_at')

        if len(verifications) > 0:
            verification = verifications[0]
            self.check_object_permissions(self.request, verification)
            return verification

        raise Http404
