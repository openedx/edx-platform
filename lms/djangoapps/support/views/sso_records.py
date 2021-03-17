"""
Views for SSO records.
"""

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework.generics import GenericAPIView
from social_django.models import UserSocialAuth

from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.support.decorators import require_support_permission
from lms.djangoapps.support.serializers import serialize_sso_records


class SsoView(GenericAPIView):
    """
    Returns a list of SSO records for a given user.
    """
    @method_decorator(require_support_permission)
    def get(self, request, username_or_email):  # lint-amnesty, pylint: disable=missing-function-docstring
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return JsonResponse([])
        user_social_auths = UserSocialAuth.objects.filter(user=user)
        sso_records = serialize_sso_records(user_social_auths)
        return JsonResponse(sso_records)
