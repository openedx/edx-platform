"""
Views for Admin Panel API
"""
import uuid

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import F, Prefetch
from organizations.models import Organization
from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from six import text_type

from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.features.pakx.lms.overrides.models import CourseProgressStats
from openedx.features.pakx.lms.overrides.utils import get_course_progress_percentage
from student.models import CourseEnrollment

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS
from .pagination import CourseEnrollmentPagination, PakxAdminAppPagination
from .permissions import CanAccessPakXAdminPanel
from .serializers import (
    BasicUserSerializer,
    LearnersSerializer,
    UserCourseEnrollmentSerializer,
    UserProfileSerializer,
    UserSerializer
)
from .utils import (
    get_learners_filter,
    get_roles_q_filters,
    get_user_org_filter,
    send_registration_email,
    specify_user_role
)


class UserCourseEnrollmentsListAPI(generics.ListAPIView):
    """
    List API of user course enrollment
    """
    serializer_class = UserCourseEnrollmentSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = CourseEnrollmentPagination
    model = CourseEnrollment

    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            user_id=self.kwargs['user_id'], is_active=True
        ).select_related(
            'course'
        ).order_by(
            '-id'
        )

    def get_serializer_context(self):
        context = super(UserCourseEnrollmentsListAPI, self).get_serializer_context()
        context.update({'request': self.request})
        return context


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

    def create(self, request, *args, **kwargs):
        profile_data = request.data.pop('profile', None)
        role = request.data.pop('role', None)
        user_serializer = BasicUserSerializer(data=request.data)
        if user_serializer.is_valid():
            with transaction.atomic():
                user = user_serializer.save()
                user.set_password(uuid.uuid4().hex[:8])
                user.save()
                profile_data['user'] = user.id
                profile_data['organization'] = Organization.objects.get(user_profiles__user=self.request.user).id
                profile_serializer = UserProfileSerializer(data=profile_data)
                if profile_serializer.is_valid():
                    user_profile = profile_serializer.save()
                    specify_user_role(user, role)
                    send_registration_email(user, user_profile, request.scheme)
                    return Response(
                        self.get_serializer(
                            self.get_queryset().filter(id=user.id).first()).data, status=status.HTTP_200_OK)
            return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        user_profile_data = request.data.pop('profile', {})
        user_data = request.data
        user_serializer = BasicUserSerializer(user, data=user_data, partial=True)
        profile_serializer = UserProfileSerializer(user.profile, data=user_profile_data, partial=True)
        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            specify_user_role(user, request.data.pop("role", None))
            return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)
        return Response({**user_serializer.errors, **profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if self.get_queryset().filter(id=kwargs['pk']).update(is_active=False):
            return Response(status=status.HTTP_200_OK)

        return Response({"ID not found": kwargs['pk']}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()

        roles = self.request.query_params['roles'].split(',') if self.request.query_params.get('roles') else []
        roles_qs = get_roles_q_filters(roles)
        if roles_qs:
            self.queryset = self.queryset.filter(roles_qs)

        username = self.request.query_params['username'] if self.request.query_params.get('username') else None
        if username:
            self.queryset = self.queryset.filter(username=username)

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

    :returns:
    {
        "count": 4,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 5,
                "name": "",
                "email": "honor@example.com",
                "last_login": "2021-06-22T05:39:30.818097Z",
                "assigned_courses": 2,
                "incomplete_courses": 1,
                "completed_courses": 1
            },
            {
                "id": 7,
                "name": "",
                "email": "verified@example.com",
                "last_login": null,
                "assigned_courses": 1,
                "incomplete_courses": 1,
                "completed_courses": 0
            }
        ]
    }
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = PakxAdminAppPagination
    serializer_class = LearnersSerializer

    def get_queryset(self):
        user_qs = User.objects.filter(get_learners_filter())
        if not self.request.user.is_superuser:
            user_qs = user_qs.filter(get_user_org_filter(self.request.user))

        course_stats = CourseProgressStats.objects.all()
        return user_qs.prefetch_related(
            Prefetch('courseprogressstats_set', to_attr='course_stats', queryset=course_stats)
        )
