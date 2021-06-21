"""
Views for Admin Panel API
"""
from django.contrib.auth.models import Group, User
from django.db.models import F, Prefetch
from django.db.models.query_utils import Q
from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from six import text_type

from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.features.pakx.lms.overrides.utils import get_course_progress_percentage
from student.models import CourseEnrollment

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS, LEARNER, ORG_ADMIN, TRAINING_MANAGER
from .pagination import PakxAdminAppPagination
from .permissions import CanAccessPakXAdminPanel
from .serializers import LearnersSerializer, UserSerializer
from .utils import get_learners_filter, get_user_org_filter


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    User view-set for user listing/create/update/active/de-active
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = PakxAdminAppPagination
    serializer_class = UserSerializer
    filter_backends = [OrderingFilter]
    OrderingFilter.ordering_fields = ('id', 'name', 'email', 'employee_id')
    ordering = ['-id']

    def destroy(self, request, *args, **kwargs):
        if self.get_queryset().filter(id=kwargs['pk']).update(is_active=False):
            return Response(status=status.HTTP_200_OK)

        return Response({"ID not found": kwargs['pk']}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        roles = self.request.query_params['roles'].split(',') if self.request.query_params.get('roles') else []
        roles_qs = self.get_roles_q_filters(roles)

        self.queryset = self.get_queryset()

        if roles_qs:
            self.queryset = self.queryset.filter(roles_qs)

        languages = self.request.query_params['languages'].split(',') if self.request.query_params.get(
            'languages') else []

        if languages:
            self.queryset = self.queryset.filter(profile__language__in=languages)

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)

        return Response(self.get_serializer(self.queryset, many=True).data)

    def get_queryset(self):
        if self.request.query_params.get("ordering"):
            self.ordering = self.request.query_params['ordering'].split(',') + self.ordering

        if self.request.user.is_superuser:
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(get_user_org_filter(self.request.user))

        group_qs = Group.objects.filter(name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN])
        return queryset.select_related(
            'profile'
        ).prefetch_related(
            Prefetch('groups', to_attr='staff_groups', queryset=group_qs),
        ).annotate(
            employee_id=F('profile__employee_id'), name=F('first_name')
        ).order_by(
            *self.ordering
        )

    def activate_users(self, request, *args, **kwargs):
        return self.change_activation_status(True, request.data["ids"])

    def deactivate_users(self, request, *args, **kwargs):
        return self.change_activation_status(False, request.data["ids"])

    def get_roles_q_filters(self, roles):
        """
        return Q filter to be used for filter user queryset
        :param roles: request params to filter roles
        :return: Q filters
        """
        qs = Q()

        for role in roles:
            if int(role) == ORG_ADMIN:
                qs |= Q(groups__name=GROUP_ORGANIZATION_ADMIN)
            elif int(role) == LEARNER:
                qs |= ~Q(Q(is_superuser=True) | Q(is_staff=True) | Q(
                    groups__name__in=[GROUP_TRAINING_MANAGERS, GROUP_TRAINING_MANAGERS]))
            elif int(role) == TRAINING_MANAGER:
                qs |= Q(groups__name=GROUP_TRAINING_MANAGERS)

        return qs

    def change_activation_status(self, activation_status, ids):
        """
        method to change user activation status for given user IDs
        :param activation_status: new boolean active status
        :param ids: user IDs to be updated
        :return: response with respective status
        """
        if ids == "all":
            self.get_queryset().all().update(is_active=activation_status)
            return Response(status=status.HTTP_200_OK)

        if self.get_queryset().filter(id__in=ids).update(is_active=activation_status):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class AnalyticsStats(views.APIView):
    """
    API view for organization level analytics stats
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get analytics quick stats about learner and their assigned courses
        """
        user_qs = User.objects.filter(get_learners_filter())

        if not self.request.user.is_superuser:
            user_qs = user_qs.filter(get_user_org_filter(self.request.user))

        user_ids = user_qs.values_list('id', flat=True)
        data = {'learner_count': len(user_ids), 'course_assignment_count': 0, 'completed_course_count': 0}

        for c_enrollment in CourseEnrollment.objects.filter(user_id__in=user_ids):
            # todo: move to figure's data for course completion once it's integrated
            grades = CourseGradeFactory().read(c_enrollment.user, course_key=c_enrollment.course.id)
            progress = get_course_progress_percentage(self.request, text_type(c_enrollment.course.id))
            if grades.passed and progress >= 100:
                data['completed_course_count'] += 1

            data['course_assignment_count'] += 1

        data['course_in_progress'] = data['course_assignment_count'] - data['completed_course_count']
        return Response(status=status.HTTP_200_OK, data=data)


class LearnerListAPI(generics.ListAPIView):
    """
    API view for learners list
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = PakxAdminAppPagination
    serializer_class = LearnersSerializer

    def get_queryset(self):
        user_qs = User.objects.filter(get_learners_filter())
        if not self.request.user.is_superuser:
            user_qs = user_qs.filter(get_user_org_filter(self.request.user))

        active_enrollments = CourseEnrollment.objects.filter(is_active=True)
        return user_qs.prefetch_related(
            Prefetch('courseenrollment_set', to_attr='enrollments', queryset=active_enrollments)
        )
