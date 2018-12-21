# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging
from django.conf import settings
from django.urls import reverse

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser

from rest_framework import filters
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from professors.models import Professor
from professors.serializers import (
    ProfessorsListSerializer,
    ProfessorDetailSerializer
)

log = logging.getLogger(__name__)


class ProfessorsListAPIView(generics.ListAPIView):
    """
    教授列表
    """
    authentication_classes = ()
    serializer_class = ProfessorsListSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('sort_num',)
    ordering = ('-sort_num',)

    def get_queryset(self):
        return Professor.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        """
        查询教授列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        result = super(ProfessorsListAPIView, self).get(request, *args, **kwargs)
        return Response(result.data)


class ProfessorDetailAPIView(generics.RetrieveAPIView):
    """
    教授详情
    """

    serializer_class = ProfessorDetailSerializer
    authentication_classes = (
    )

    def get(self, request, pk, *args, **kwargs):
        """
        查询教授详情信息
        :param request:
        :param pk:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            instance = Professor.objects.get(id=pk, is_active=True)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as ex:
            log.error(ex)
            return Response({})
