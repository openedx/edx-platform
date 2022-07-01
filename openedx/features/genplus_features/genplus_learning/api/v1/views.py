from rest_framework import generics, status, views, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Student
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudentOrTeacher, IsTeacher
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment
from .serializers import LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """
    Viewset for Lessons APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
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

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
        if self.action == 'list':
            permission_classes.append(IsStudentOrTeacher)
        else:
            permission_classes.append(IsTeacher)
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['put'])
    def unlock_lesson(self, request, pk=None):  # pylint: disable=unused-argument
        """
       unlock the lesson of the unit
        """
        lesson = self.get_object()
        if not lesson.is_locked:
            return Response(ErrorMessages.LESSON_ALREADY_UNLOCKED, status.HTTP_204_NO_CONTENT)
        lesson.is_locked = False
        lesson.save()
        return Response(SuccessMessages.LESSON_UNLOCKED, status.HTTP_204_NO_CONTENT)

