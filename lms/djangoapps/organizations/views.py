# pylint: disable=C0103

""" ORGANIZATIONS API VIEWS """
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, F, Count

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api_manager.courseware_access import get_course_key, get_aggregate_exclusion_user_ids
from organizations.models import Organization
from api_manager.users.serializers import UserSerializer, SimpleUserSerializer
from api_manager.groups.serializers import GroupSerializer
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

    @action(methods=['get', ])
    def metrics(self, request, pk):
        """
        Provide statistical information for the specified Organization
        """
        response_data = {}
        grade_avg = 0
        grade_complete_match_range = getattr(settings, 'GRADEBOOK_GRADE_COMPLETE_PROFORMA_MATCH_RANGE', 0.01)
        org_user_grades = StudentGradebook.objects.filter(user__organizations=pk, user__is_active=True)
        courses_filter = request.QUERY_PARAMS.get('courses', None)
        courses = []
        exclude_users = set()
        if courses_filter:
            upper_bound = getattr(settings, 'API_LOOKUP_UPPER_BOUND', 100)
            courses_filter = courses_filter.split(",")[:upper_bound]
            for course_string in courses_filter:
                courses.append(get_course_key(course_string))

            # fill exclude users
            for course_key in courses:
                exclude_users.union(get_aggregate_exclusion_user_ids(course_key))

            org_user_grades = org_user_grades.filter(course_id__in=courses).exclude(user_id__in=exclude_users)

        users_grade_sum = org_user_grades.aggregate(Sum('grade'))
        if users_grade_sum['grade__sum']:
            users_enrolled_qs = CourseEnrollment.objects.filter(user__is_active=True, is_active=True,
                                                                user__organizations=pk)\
                .exclude(user_id__in=exclude_users)
            if courses:
                users_enrolled_qs = users_enrolled_qs.filter(course_id__in=courses)
            users_enrolled = users_enrolled_qs.aggregate(Count('user', distinct=True))
            total_users = users_enrolled['user__count']
            if total_users:
                # in order to compute avg across organization we need course of courses org has
                total_courses_in_org = len(courses)
                if not courses:
                    org_courses = users_enrolled_qs.aggregate(Count('course_id', distinct=True))
                    total_courses_in_org = org_courses['course_id__count']
                grade_avg = float('{0:.3f}'.format(
                    float(users_grade_sum['grade__sum']) / total_users / total_courses_in_org
                ))
        response_data['users_grade_average'] = grade_avg

        users_grade_complete_count = org_user_grades\
            .filter(proforma_grade__lte=F('grade') + grade_complete_match_range, proforma_grade__gt=0)\
            .aggregate(Count('user', distinct=True))
        response_data['users_grade_complete_count'] = users_grade_complete_count['user__count'] or 0

        return Response(response_data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'])
    def users(self, request, pk):
        """
        - URI: ```/api/organizations/{org_id}/users/```
        - GET: Returns users in an organization
            * course_id parameter should filter user by course
            * include_course_counts parameter should be `true` to get user's enrollment count
            * include_grades parameter should be `true` to get user's grades
            * for the course given in the course_id parameter
        - POST: Adds a User to an Organization

        """
        if request.method == 'GET':
            include_course_counts = request.QUERY_PARAMS.get('include_course_counts', None)
            include_grades = request.QUERY_PARAMS.get('include_grades', None)
            course_id = request.QUERY_PARAMS.get('course_id', None)
            grade_complete_match_range = getattr(settings, 'GRADEBOOK_GRADE_COMPLETE_PROFORMA_MATCH_RANGE', 0.01)
            course_key = None
            if course_id:
                course_key = get_course_key(course_id)

            users = User.objects.filter(organizations=pk)

            if course_key:
                users = users.filter(courseenrollment__course_id__exact=course_key,
                                     courseenrollment__is_active=True)
            if str2bool(include_grades):
                users = users.select_related('studentgradebook')

            if str2bool(include_course_counts):
                enrollments = CourseEnrollment.objects.filter(user__in=users).values('user').order_by().annotate(total=Count('user'))
                enrollments_by_user = {}
                for enrollment in enrollments:
                    enrollments_by_user[enrollment['user']] = enrollment['total']

            response_data = []
            if users:
                for user in users:
                    serializer = SimpleUserSerializer(user)
                    user_data = serializer.data

                    if str2bool(include_course_counts):
                        user_data['course_count'] = enrollments_by_user.get(user.id, 0)

                    if str2bool(include_grades) and course_key:
                        user_grades = {'grade': 0, 'proforma_grade': 0, 'complete_status': False}
                        gradebook = user.studentgradebook_set.filter(course_id=course_key)
                        if gradebook:
                            user_grades['grade'] = gradebook[0].grade
                            user_grades['proforma_grade'] = gradebook[0].proforma_grade
                            user_grades['complete_status'] = True if 0 < gradebook[0].proforma_grade <= \
                                gradebook[0].grade + grade_complete_match_range else False
                        user_data.update(user_grades)

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

    @action(methods=['get', 'post'])
    def groups(self, request, pk):
        """
        Add a Group to a organization or retrieve list of groups in organization
        """
        if request.method == 'GET':
            group_type = request.QUERY_PARAMS.get('type', None)
            groups = Group.objects.filter(organizations=pk)
            if group_type:
                groups = groups.filter(groupprofile__group_type=group_type)
            response_data = []
            if groups:
                for group in groups:
                    serializer = GroupSerializer(group)
                    response_data.append(serializer.data)  # pylint: disable=E1101
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            group_id = request.DATA.get('id')
            try:
                group = Group.objects.get(id=group_id)
            except ObjectDoesNotExist:
                message = 'Group {} does not exist'.format(group_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            organization = self.get_object()
            organization.groups.add(group)
            organization.save()
            return Response({}, status=status.HTTP_201_CREATED)
