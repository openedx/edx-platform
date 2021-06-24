"""
Views for Admin Panel API
"""
import uuid

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import F, Prefetch, Q
from django.http import Http404
from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from openedx.features.pakx.lms.overrides.models import CourseProgressStats
from student.models import CourseEnrollment

from .constants import GROUP_ORGANIZATION_ADMIN, GROUP_TRAINING_MANAGERS, ORG_ADMIN, TRAINING_MANAGER
from .pagination import CourseEnrollmentPagination, PakxAdminAppPagination
from .permissions import CanAccessPakXAdminPanel
from .serializers import (
    BasicUserSerializer,
    LearnersSerializer,
    UserCourseEnrollmentSerializer,
    UserDetailViewSerializer,
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
            user_id=self.kwargs['user_id'], is_active=True,
            user__profile=self.request.user.profile.organization_id
        ).select_related(
            'course'
        ).prefetch_related(
            'user__courseprogressstats_set'
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
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = PakxAdminAppPagination
    serializer_class = UserSerializer
    filter_backends = [OrderingFilter]
    OrderingFilter.ordering_fields = ('id', 'name', 'email', 'employee_id')
    ordering = ['-id']

    def get_object(self):
        user_obj = User.objects.filter(
            id=self.kwargs['pk']
        ).select_related(
            'profile'
        ).prefetch_related(
            'courseprogressstats_set'
        ).first()

        if user_obj:
            return user_obj
        raise Http404

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create']:
            return UserDetailViewSerializer

        return UserSerializer

    def create(self, request, *args, **kwargs):
        profile_data = request.data.pop('profile', None)
        role = request.data.pop('role', None)

        user_serializer = BasicUserSerializer(data=request.data)
        profile_serializer = UserProfileSerializer(data=profile_data)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            with transaction.atomic():
                user = user_serializer.save()
                user.set_password(uuid.uuid4().hex[:8])
                user.save()

                profile_data['user'] = user.id
                profile_data['organization'] = self.request.user.profile.organization_id
                user_profile = profile_serializer.save()
                specify_user_role(user, role)
                send_registration_email(user, user_profile, request.scheme)

                return Response(self.get_serializer(user), status=status.HTTP_201_CREATED)

        return Response({**user_serializer.errors, **profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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

        search = self.request.query_params.get('search', '').strip()
        for s_text in search.split():
            self.queryset = self.queryset.filter(
                Q(first_name__contains=s_text) | Q(last_name__contains=s_text) | Q(email__contains=s_text)
            )

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
            queryset = User.objects.filter(**get_user_org_filter(self.request.user))

        group_qs = Group.objects.filter(name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN]).order_by('name')
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
            user_qs = user_qs.filter(**get_user_org_filter(self.request.user))

        user_ids = user_qs.values_list('id', flat=True)
        data = {'learner_count': len(user_ids), 'course_assignment_count': 0, 'completed_course_count': 0}

        for course_stats in CourseProgressStats.objects.filter(user_id__in=user_ids):
            if course_stats.email_reminder_status == CourseProgressStats.COURSE_COMPLETED:
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
            user_qs = user_qs.filter(**get_user_org_filter(self.request.user))

        course_stats = CourseProgressStats.objects.all()
        return user_qs.prefetch_related(
            Prefetch('courseprogressstats_set', to_attr='course_stats', queryset=course_stats)
        )


class UserInfo(views.APIView):
    """
    API for basic user information
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        user_info = {
            'name': self.request.user.get_full_name(),
            'username': self.request.user.username,
            'is_superuser': self.request.user.is_superuser,
            'role': None
        }
        user_groups = Group.objects.filter(
            user=self.request.user, name__in=[GROUP_TRAINING_MANAGERS, GROUP_ORGANIZATION_ADMIN]
        ).order_by('name').first()
        if user_groups:
            user_info['role'] = TRAINING_MANAGER if user_groups.name == GROUP_TRAINING_MANAGERS else ORG_ADMIN

        return Response(status=status.HTTP_200_OK, data=user_info)
