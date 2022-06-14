from dateutil.parser import parse
from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models import ExpressionWrapper, F, IntegerField, Prefetch, Q, Sum
from django.http import Http404, HttpResponse
from django.middleware import csrf
from django.utils.decorators import method_decorator

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.features.genplus_features.genplus.models import GenUser

class UserInfo(views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        try:
            gen_user_role = GenUser.objects.get(user=self.request.user).role
        except GenUser.DoesNotExist:
            gen_user_role = None

        user_info = {
            'id': self.request.user.id,
            'name': self.request.user.profile.name,
            'username': self.request.user.username,
            'csrf_token': csrf.get_token(self.request),
            'role': gen_user_role
        }
        return Response(status=status.HTTP_200_OK, data=user_info)
