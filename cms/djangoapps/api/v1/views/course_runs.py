from django.conf import settings
from django.http import Http404
from edx_rest_framework_extensions.authentication import JwtAuthentication
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from contentstore.views.course import _accessible_courses_iter, get_course_and_check_access
from ..serializers.course_runs import CourseRunCreateSerializer, CourseRunRerunSerializer, CourseRunSerializer


class CourseRunViewSet(viewsets.ViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    lookup_value_regex = settings.COURSE_KEY_REGEX
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CourseRunSerializer

    def get_course_run_or_raise_404(self, course_run_key, user):
        course_run = get_course_and_check_access(course_run_key, user)
        if course_run:
            return course_run

        raise Http404

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def list(self, request):
        course_runs, __ = _accessible_courses_iter(request)
        serializer = self.get_serializer(course_runs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        course_run_key = CourseKey.from_string(pk)
        course_run = self.get_course_run_or_raise_404(course_run_key, request.user)
        serializer = self.get_serializer(course_run)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        course_run_key = CourseKey.from_string(pk)
        course_run = self.get_course_run_or_raise_404(course_run_key, request.user)

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(course_run, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = CourseRunCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def rerun(self, request, pk=None):
        course_run_key = CourseKey.from_string(pk)
        user = request.user
        course_run = self.get_course_run_or_raise_404(course_run_key, user)
        serializer = CourseRunRerunSerializer(course_run, data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        new_course_run = serializer.save()
        serializer = self.get_serializer(new_course_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
