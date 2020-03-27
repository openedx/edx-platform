"""
Implementation of api functions for Photo Verification.
"""

import logging
from django.utils.decorators import method_decorator
from rest_framework.generics import GenericAPIView
from lms.djangoapps.support.decorators import require_support_permission
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Q
from lms.djangoapps.verify_student.services import IDVerificationService

log = logging.getLogger(__name__)

class PhotoVerificationStatusDetail(GenericAPIView):

    authentication_classes = (JwtAuthentication,)

    @method_decorator(require_support_permission)
    def get(self, request, username):

        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            msg = 'Could not find edx account with {}'.format(username)
            log.info(msg)

            return Response({
                'user-verification-result': {},
                'msg': msg,
            }, status=status.HTTP_404_NOT_FOUND)

        user_status = IDVerificationService.user_status(user)
        if not user_status['status']:
            msg = 'Could not find verification attempt for account {}'.format(username)
            log.info(msg)

            return Response({
                'user-verification-result': {},
                'msg': msg,
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'user-verification-result': user_status
        }, status=status.HTTP_200_OK)

