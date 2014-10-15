# pylint: disable=C0103

""" ORGANIZATIONS API VIEWS """
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, F

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api_manager.courseware_access import get_course_key
from api_manager.models import Organization
from api_manager.users.serializers import UserSerializer
from api_manager.utils import str2bool
from gradebook.models import StudentGradebook
from student.models import CourseEnrollment

from .serializers import OrganizationSerializer


class OrganizationsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Organization model.
    """
    serializer_class = OrganizationSerializer
    model = Organization

    @action(methods=['get',])
    def metrics(self, request, pk):
        """
        Provide statistical information for the specified Organization
        """
        response_data = {}
        grade_avg = 0
        grade_complete_match_range = getattr(settings, 'GRADEBOOK_GRADE_COMPLETE_PROFORMA_MATCH_RANGE', 0.01)
        org_user_grades = StudentGradebook.objects.filter(user__organizations=pk, user__is_active=True)
        courses_filter = request.QUERY_PARAMS.get('courses', None)
        if courses_filter:
            upper_bound = getattr(settings, 'API_LOOKUP_UPPER_BOUND', 100)
            courses_filter = courses_filter.split(",")[:upper_bound]
            courses = []
            for course_string in courses_filter:
                courses.append(get_course_key(course_string))
            org_user_grades = org_user_grades.filter(course_id__in=courses)

        users_grade_average = org_user_grades.aggregate(Avg('grade'))
        if users_grade_average['grade__avg']:
            grade_avg = float('{0:.3f}'.format(float(users_grade_average['grade__avg'])))
        response_data['users_grade_average'] = grade_avg

        users_grade_complete_count = org_user_grades\
            .filter(proforma_grade__lte=F('grade') + grade_complete_match_range, proforma_grade__gt=0).count()
        response_data['users_grade_complete_count'] = users_grade_complete_count

        return Response(response_data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'])
    def users(self, request, pk):
        """
        Add a User to an Organization
        """
        if request.method == 'GET':
            include_course_counts = request.QUERY_PARAMS.get('include_course_counts', None)
            users = User.objects.filter(organizations=pk)
            response_data = []
            if users:
                for user in users:
                    serializer = UserSerializer(user)
                    user_data = serializer.data
                    if str2bool(include_course_counts):
                        enrollments = CourseEnrollment.enrollments_for_user(user).count()
                        user_data['course_count'] = enrollments
                    response_data.append(user_data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            user_id = request.DATA.get('id')
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                message = 'User {} does not exist'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            organization = self.get_object()
            organization.users.add(user)
            organization.save()
            return Response({}, status=status.HTTP_201_CREATED)
