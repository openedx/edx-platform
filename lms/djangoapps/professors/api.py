# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging

from rest_framework import filters
from rest_framework import generics
from rest_framework.response import Response
from opaque_keys.edx.keys import CourseKey
from professors.models import Professor, ProfessorCourses
from professors.serializers import (
    ProfessorsListSerializer,
    ProfessorDetailSerializer,
    ProfessorCoursesListSerializer,
    CourseProfessorSerializer
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


class ProfessorCoursesListAPIView(generics.ListAPIView):
    """
    教授授课课程列表
    """
    authentication_classes = ()
    serializer_class = ProfessorCoursesListSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('sort_num',)
    ordering = ('-sort_num',)

    def get_queryset(self):
        return ProfessorCourses.objects.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        """
        查询教授授课课程列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        result = super(ProfessorCoursesListAPIView, self).get(request, *args, **kwargs)
        return Response(result.data)


class CourseProfessorAPIView(generics.RetrieveAPIView):
    """
    课程所属教授
    """
    serializer_class = CourseProfessorSerializer
    authentication_classes = (
    )

    def get(self, request, course_id, *args, **kwargs):
        """
        课程所属教授
        :param request:
        :param course_id:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            course_key = CourseKey.from_string(course_id)
            instance = ProfessorCourses.objects.get(course_id=course_key, is_active=True)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as ex:
            log.error(ex)
            return Response({})
