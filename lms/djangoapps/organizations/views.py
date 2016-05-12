# pylint: disable=C0103

""" ORGANIZATIONS API VIEWS """
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, F, Count
from django.db import IntegrityError
from django.utils.translation import ugettext as _

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from api_manager.courseware_access import get_course_key, get_course_descriptor
from api_manager.courses.serializers import OrganizationCourseSerializer
from organizations.models import Organization, OrganizationGroupUser
from api_manager.users.serializers import SimpleUserSerializer
from api_manager.groups.serializers import GroupSerializer
from api_manager.permissions import SecureListAPIView
from api_manager.utils import str2bool
from gradebook.models import StudentGradebook
from student.models import CourseEnrollment
from student.roles import get_aggregate_exclusion_user_ids

from .serializers import OrganizationSerializer, BasicOrganizationSerializer


class OrganizationsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Organization model.
    """
    serializer_class = OrganizationSerializer
    model = Organization

    def list(self, request, *args, **kwargs):
        self.serializer_class = BasicOrganizationSerializer
        return super(OrganizationsViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = BasicOrganizationSerializer
        return super(OrganizationsViewSet, self).retrieve(request, *args, **kwargs)

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

    @action(methods=['get', 'post', 'delete'])
    def users(self, request, pk):
        """
        - URI: ```/api/organizations/{org_id}/users/```
        - GET: Returns users in an organization
            * course_id parameter should filter user by course
            * include_course_counts parameter should be `true` to get user's enrollment count
            * include_grades parameter should be `true` to get user's grades
            * for the course given in the course_id parameter
            * view parameter can be used to get a particular data .i.e. view=ids to
            * get list of user ids
        - POST: Adds a User to an Organization
        - DELETE: Removes the user(s) given in the `users` param from an Organization.
        """
        if request.method == 'GET':
            include_course_counts = request.QUERY_PARAMS.get('include_course_counts', None)
            include_grades = request.QUERY_PARAMS.get('include_grades', None)
            course_id = request.QUERY_PARAMS.get('course_id', None)
            view = request.QUERY_PARAMS.get('view', None)
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

            # if we only need ids of users in organization return now
            if view == 'ids':
                user_ids = users.values_list('id', flat=True)
                return Response(user_ids)

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
        elif request.method == 'DELETE':
            user_ids = request.DATA.get('users')
            if not user_ids:
                return Response({"detail": _('users parameter is missing.')}, status.HTTP_400_BAD_REQUEST)
            try:
                user_ids = [int(user_id) for user_id in filter(None, user_ids.split(','))]
            except ValueError:
                return Response({
                    "detail": _('users parameter must be comma separated list of integers.')
                }, status.HTTP_400_BAD_REQUEST)

            organization = self.get_object()
            users_to_be_deleted = organization.users.filter(id__in=user_ids)
            total_users = len(users_to_be_deleted)
            for user in users_to_be_deleted:
                organization.users.remove(user)
            if total_users > 0:
                return Response({
                    "detail": _("{users_removed} user(s) removed from organization").format(users_removed=total_users)
                }, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
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
        - GET: Returns groups in an organization
            * view parameter can be used to get a particular data .i.e. view=ids to
            * get list of group ids

        """
        if request.method == 'GET':
            group_type = request.QUERY_PARAMS.get('type', None)
            view = request.QUERY_PARAMS.get('view', None)
            groups = Group.objects.filter(organizations=pk)

            if group_type:
                groups = groups.filter(groupprofile__group_type=group_type)

            # if we only need ids of groups in organization return now
            if view == 'ids':
                group_ids = groups.values_list('id', flat=True)
                return Response(group_ids)

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

    @action(methods=['get', ])
    def courses(self, request, pk):  # pylint: disable=W0613
        """
        Returns list of courses in an organization
        """
        organization = self.get_object()
        course_ids = Group.objects.filter(organizations=organization)\
            .values_list('coursegrouprelationship__course_id', flat=True).distinct()
        course_keys = map(get_course_key, filter(None, course_ids))
        enrollment_qs = CourseEnrollment.objects.filter(is_active=True, course_id__in=course_keys)\
            .values_list('course_id', 'user_id')

        enrollments = {}
        for (course_id, user_id) in enrollment_qs:
            enrollments.setdefault(course_id, []).append(user_id)

        response_data = []
        for course_key in course_keys:
            course_descriptor = get_course_descriptor(course_key, 0)
            if course_descriptor is not None:
                enrolled_users = enrollments.get(unicode(course_key), [])
                setattr(course_descriptor, 'enrolled_users', enrolled_users)
                response_data.append(course_descriptor)

        serializer = OrganizationCourseSerializer(response_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationsGroupsUsersList(SecureListAPIView):
    """
    OrganizationsGroupsUsersList returns a collection of users for a organization group.

    **Example Request**

        GET /api/organizations/{organization_id}/groups/{group_id}/users

        POST /api/organizations/{organization_id}/groups/{group_id}/users

        DELETE /api/organizations/{organization_id}/groups/{group_id}/users

    ### The OrganizationsGroupsUsersList view allows clients to retrieve a list of users for a given organization group
    - URI: ```/api/organizations/{organization_id}/groups/{group_id}/users```
    - GET: Returns a JSON representation (array) of the set of User entities
    - POST: Creates a new relationship between the provided User, Group and Organization
        * users: __required__, The identifier for the User with which we're establishing relationship
    - POST Example:

            {
                "users" : 1,2,3,4,5
            }

    - DELETE: Deletes a relationship between the provided User, Group and Organization
        * users: __required__, The identifier for the User for which we're removing relationship
    - DELETE Example:

            {
                "users" : 1,2,3,4,5
            }
    """

    model = OrganizationGroupUser

    def get(self, request, organization_id, group_id):  # pylint: disable=W0221
        """
        GET /api/organizations/{organization_id}/groups/{group_id}/users
        """
        queryset = User.objects.filter(organizationgroupuser__group_id=group_id,
                                       organizationgroupuser__organization_id=organization_id)

        serializer = SimpleUserSerializer(queryset, many=True)

        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request, organization_id, group_id):
        """
        GET /api/organizations/{organization_id}/groups/{group_id}/users
        """
        user_ids = request.DATA.get('users')
        try:
            user_ids = map(int, filter(None, user_ids.split(',')))
        except Exception:
            raise ParseError("Invalid user id value")

        try:
            group = Group.objects.get(id=group_id, organizations=organization_id)
        except ObjectDoesNotExist:
            return Response({
                "detail": 'Group {} does not belong to organization {}'.format(group_id, organization_id)
            }, status.HTTP_404_NOT_FOUND)

        users_added = []
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                OrganizationGroupUser.objects.create(organization_id=organization_id, group=group, user=user)
            except (ObjectDoesNotExist, IntegrityError):
                continue

            users_added.append(str(user_id))

        if len(users_added) > 0:
            return Response({
                "detail": "user id(s) {users_added} added to organization {org_id}'s group {group_id}"
                          .format(users_added=', '.join(users_added), org_id=organization_id, group_id=group_id)
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, organization_id, group_id):
        """
        DELETE /api/organizations/{organization_id}/groups/{group_id}/users
        """
        user_ids = request.DATA.get('users')
        try:
            user_ids = map(int, filter(None, user_ids.split(',')))
        except Exception:
            raise ParseError("Invalid user id value")

        try:
            group = Group.objects.get(id=group_id, organizations=organization_id)
        except ObjectDoesNotExist:
            return Response({
                "detail": 'Group {} does not belong to organization {}'.format(group_id, organization_id)
            }, status.HTTP_404_NOT_FOUND)

        organization_group_users_to_delete = OrganizationGroupUser.objects.filter(organization_id=organization_id,
                                                                                  user_id__in=user_ids,
                                                                                  group=group)
        org_group_user_ids = [str(org_group_user.user_id) for org_group_user in organization_group_users_to_delete]
        organization_group_users_to_delete.delete()

        if len(org_group_user_ids) > 0:
            org_group_user_ids = ', '.join(org_group_user_ids)
            message = "user id(s) {org_group_user_ids} removed from organization {org_id}'s group {group_id}"\
                      .format(org_group_user_ids=org_group_user_ids, org_id=organization_id, group_id=group_id)
            return Response({
                "detail": message
            }, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
