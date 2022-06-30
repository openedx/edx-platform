from rest_framework import generics, status, views, viewsets
from rest_framework.permissions import IsAuthenticated

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment
from .serializers import LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = Program.get_current_programs()
        gen_user = self.request.user.gen_user
        if gen_user.is_student:
            student_enrolled_programs = ProgramEnrollment.objects.filter(
                gen_user=gen_user
            ).values_list('program', flat=True)
            qs = qs.filter(id__in=student_enrolled_programs)

        return qs

    def get_serializer_context(self):
        context = super(LessonViewSet, self).get_serializer_context()
        context.update({"gen_user": self.request.user.gen_user})
        return context
