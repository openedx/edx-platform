""" Verification API v1 views. """
from django.http import Http404
from rest_framework.generics import RetrieveAPIView

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.user_api.serializers import SoftwareSecurePhotoVerificationSerializer
from openedx.core.lib.api.permissions import IsStaffOrOwner
from openedx.core.lib.api.view_utils import view_auth_classes


@view_auth_classes(permission_classes=(IsStaffOrOwner,))
class PhotoVerificationStatusView(RetrieveAPIView):
    """ PhotoVerificationStatus detail endpoint. """
    serializer_class = SoftwareSecurePhotoVerificationSerializer

    def get_object(self):
        username = self.kwargs['username']
        verifications = SoftwareSecurePhotoVerification.objects.filter(user__username=username).order_by('-updated_at')

        if len(verifications) > 0:
            verification = verifications[0]
            self.check_object_permissions(self.request, verification)
            return verification

        raise Http404
