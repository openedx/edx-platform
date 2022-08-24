from django.shortcuts import get_object_or_404
from rest_framework import generics, status, views, viewsets, mixins, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student, Class
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher, IsTeacher
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment, ClassUnit
from .serializers import ProgramSerializer, ClassStudentSerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    serializer_class = ProgramSerializer

    def get_queryset(self):
        gen_user = self.request.user.gen_user
        qs = Program.get_active_programs()
        if gen_user.is_student:
            enrollments = ProgramEnrollment.objects.filter(student=gen_user.student)
            program_ids = enrollments.values_list('program', flat=True)
            qs = Program.objects.filter(id__in=program_ids)
        return qs

    def get_serializer_context(self):
        context = super(ProgramViewSet, self).get_serializer_context()
        context.update({
            "gen_user": self.request.user.gen_user,
        })
        return context

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
        if self.action == 'list':
            permission_classes.append(IsStudentOrTeacher)
        else:
            permission_classes.append(IsTeacher)
        return [permission() for permission in permission_classes]


class ClassStudentViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassStudentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['gen_user__user__username']

    def get_serializer_context(self):
        context = super(ClassStudentViewSet, self).get_serializer_context()
        group_id = self.kwargs.get('group_id', None)
        if group_id:
            gen_class = get_object_or_404(Class, group_id=group_id)
            class_units = ClassUnit.objects.select_related('unit')
            context['class_units'] = class_units.filter(gen_class=gen_class).order_by('unit__order')
            context['request'] = self.request
            return context

    def get_queryset(self):
        group_id = self.kwargs.get('group_id', None)
        try:
            gen_class = Class.objects.prefetch_related('students').get(group_id=group_id)
        except Class.DoesNotExist:
            return Student.objects.none()
        return gen_class.students.select_related('gen_user__user').all()
