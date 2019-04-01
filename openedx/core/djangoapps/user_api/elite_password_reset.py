"""elite password reset user API. """

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication

from util.json_request import JsonResponse
from util.password_policy_validators import normalize_password, validate_password


class ElitePasswordResetView(APIView):
    """ elite password reset """
    
    authentication_classes = (
        SessionAuthenticationAllowInactiveUser, JwtAuthentication, OAuth2AuthenticationAllowInactiveUser)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        
        old_password = request.POST['old_password']
        new_password1 = request.POST['new_password1']
        new_password2 = request.POST['new_password2']
        user = request.user
        password = new_password1
           
        if user.check_password(old_password):    
            if new_password1 != new_password2:
                return JsonResponse({'result': 'failed', 'code': 201, 'msg': _('New passwords do not match. Please try again.')})
            try:
                validate_password(password, user=user)
            except ValidationError as err:
                return JsonResponse({'result': 'failed', 'code': 202, 'msg': ' '.join(err.messages)})                    
            user.set_password(password)
            user.save() 
            return JsonResponse({'result': 'success', 'code': 200, 'msg': _('Password modified.')})
        else:
            return JsonResponse({'result': 'failed', 'code': 203, 'msg': _('Wrong password')})
            