from rest_framework import generics, status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher, IsTeacher
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment
from .serializers import ProgramSerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    serializer_class = ProgramSerializer

    def get_queryset(self):
        gen_user = self.request.user.gen_user
        qs = Program.get_current_programs()
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
