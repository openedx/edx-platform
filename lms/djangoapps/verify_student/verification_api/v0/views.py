""" Verification API v0 views. """
from django.http import Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_oauth.authentication import OAuth2Authentication

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.verification_api.v0.serializers import SoftwareSecurePhotoVerificationSerializer
from openedx.core.lib.api.permissions import IsStaffOrOwner


class PhotoVerificationStatusView(RetrieveAPIView):
    """ PhotoVerificationStatus detail endpoint. """
    lookup_url_kwarg = 'username'
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated, IsStaffOrOwner,)
    serializer_class = SoftwareSecurePhotoVerificationSerializer

    def get_object(self):
        username = self.kwargs[self.lookup_url_kwarg]
        print username
        verifications = SoftwareSecurePhotoVerification.objects.filter(user__username=username) \
            .order_by('-updated_at').select_related('user')

        if len(verifications) > 0:
            verification = verifications[0]
            self.check_object_permissions(self.request, verification)
            return verification

        raise Http404
