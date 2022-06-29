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
        genuser = self.request.user.genuser
        if genuser.is_student:
            student_enrolled_programs = ProgramEnrollment.objects.filter(
                student=genuser.student
            ).values_list('program', flat=True)
            qs = qs.filter(id__in=student_enrolled_programs)

        return qs
