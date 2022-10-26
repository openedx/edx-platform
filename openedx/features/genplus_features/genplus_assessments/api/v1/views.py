import logging
from rest_framework import views, viewsets
from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer
from openedx.features.genplus_features.genplus_assessments.utils import (
    build_students_result,
)

log = logging.getLogger(__name__)


class StudentAnswersView(viewsets.ViewSet):
    
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def students_problem_response(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        student_id = request.query_params.get('student_id',None)
        students = []
        if student_id == "all":
            students = list(Class.objects.prefetch_related('students').get(pk=class_id).students.values_list('gen_user__user_id',flat=True))
        else:
            students.append(student_id)
        course_id = request.query_params.get('course_id',None)
        course_keys = CourseKey.from_string(course_id)
        problem_locations = request.query_params.get('problem_locations',None)
        filter = request.query_params.get('filter',None)

        response = build_students_result(
            user_id = self.request.user.id,
            course_key = course_keys,
            usage_key_str = problem_locations,
            student_list = students,
            filter = filter,
        )

        return Response(response)     

class ClassFilterViewSet(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer

    def get(self,request, **kwargs):
        class_id = kwargs.get('class_id', None)
        try:
            gen_class = Class.objects.get(pk=class_id)
            data = ClassSerializer(gen_class).data
        except Class.DoesNotExist:
            return Class.objects.none()
        return Response(data)


