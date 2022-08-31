from django.middleware import csrf
from django.http import Http404
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import (
    GenUser, Character, Class, Teacher, Student, TeacherClass, JournalPost, Skill
)
from openedx.features.genplus_features.genplus.constants import JournalTypes
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from .serializers import (
    CharacterSerializer,
    ClassSerializer,
    FavoriteClassSerializer,
    UserInfoSerializer,
    JournalListSerializer,
    StudentPostSerializer,
    TeacherFeedbackSerializer,
    SkillSerializer
)
from .permissions import IsStudent, IsTeacher, IsStudentOrTeacher, IsGenUser
from .mixins import GenzMixin


class UserInfo(GenzMixin, views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsGenUser]

    @swagger_auto_schema(
        responses={200: UserInfoSerializer},
        tags=['Users'],
    )
    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        user_info = UserInfoSerializer(self.request.user, context={
            'request': self.request,
            'gen_user': self.gen_user
        })

        return Response(status=status.HTTP_200_OK, data=user_info.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Image',
                openapi.IN_QUERY,
                description='Profile image (should be in body, it shows\
                 query because only serializers or schema are allowed)',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_BASE64,
            ),
        ],
        responses={200: SuccessMessages.PROFILE_IMAGE_UPDATED},
        tags=['Users'],
    )
    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        update user's profile image
        """
        try:
            if self.gen_user.is_teacher:
                image = self.request.data.get('image', None)
                if not image:
                    raise ValueError('image field was empty')
                teacher = Teacher.objects.get(gen_user=self.gen_user)
                teacher.profile_image = image
                teacher.save()

            if self.gen_user.is_student:
                character = self.request.data.get('character', None)
                if not character:
                    raise ValueError('character field was empty')
                new_character = Character.objects.get(id=int(character))
                student = Student.objects.get(gen_user=self.gen_user)
                student.character = new_character
                student.save()

            return Response(SuccessMessages.PROFILE_IMAGE_UPDATED, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


class CharacterViewSet(GenzMixin, viewsets.ModelViewSet):
    """
    Viewset for character APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()

    @action(detail=True, methods=['put'])
    def select_character(self, request, pk=None):  # pylint: disable=unused-argument
        """
        select character at the time of onboarding or changing character from
        the profile
        """
        character = self.get_object()
        student = Student.objects.get(gen_user=self.gen_user)
        student.character = character
        if request.data.get("onboarded") and not self.gen_user.student.onboarded:
            student.onboarded = True

        student.save()
        return Response(SuccessMessages.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)


class ClassViewSet(GenzMixin, viewsets.ModelViewSet):
    """
    Viewset for class APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer
    lookup_field = 'group_id'

    def get_queryset(self):
        return Class.visible_objects.filter(school=self.school)

    def list(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        favourite_classes = self.gen_user.teacher.classes.filter(teacherclass__is_favorite=True)
        favourite_classes_serializer = self.get_serializer(favourite_classes, many=True)
        class_queryset = self.filter_queryset(self.get_queryset())
        class_serializer = self.get_serializer(
            class_queryset.exclude(group_id__in=favourite_classes.values('group_id', )),
            many=True)
        data = {
            'favourite_classes': favourite_classes_serializer.data,
            'classes': class_serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def add_my_class(self, request, group_id=None):  # pylint: disable=unused-argument
        """
        add classes to the my classes for teacher
        """
        serializer = FavoriteClassSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        gen_class = self.get_object()
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        teacher_class = TeacherClass.objects.get(teacher=teacher, gen_class=gen_class)
        if data['action'] == 'add':
            teacher_class.is_favorite = True
            teacher_class.save()
            return Response(SuccessMessages.CLASS_ADDED_TO_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)
        else:
            teacher_class.is_favorite = False
            teacher_class.save()
            return Response(SuccessMessages.CLASS_REMOVED_FROM_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)


class JournalViewSet(GenzMixin, viewsets.ModelViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']
    ordering = ['-created']

    def get_queryset(self):
        query_params = self.request.query_params
        journal_posts = JournalPost.objects.select_related('student', 'teacher', 'skill')
        if self.gen_user.is_student:
            journal_posts = journal_posts.filter(student=self.gen_user.student)
        else:
            student_id = query_params.get('student_id')
            if student_id:
                journal_posts = journal_posts.filter(student__id=student_id)
            else:
                journal_posts = JournalPost.objects.none()

        skill = query_params.get('skill')
        if skill:
            journal_posts = journal_posts.filter(skill__name__iexact=skill)

        return journal_posts.order_by(*self.ordering)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        skill_qs = Skill.objects.all()
        skills = SkillSerializer(skill_qs, many=True).data
        page = self.paginate_queryset(queryset)

        if page is not None:
            data = self.get_serializer(page, many=True).data
            response = self.get_paginated_response(data)
            response.data['skills'] = skills
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if self.gen_user.is_student:
            data = self._create_journal_post_data(request.data, JournalTypes.STUDENT_POST)
            success_message = SuccessMessages.STUDENT_POST_CREATED
            error_message = ErrorMessages.STUDENT_POST_ENTRY_FAILED
        elif self.gen_user.is_teacher:
            data = self._create_journal_post_data(request.data, JournalTypes.TEACHER_FEEDBACK)
            success_message = SuccessMessages.TEACHER_FEEDBACK_ADDED
            error_message = ErrorMessages.TEACHER_FEEDBACK_ENTRY_FAILED

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(success_message, status=status.HTTP_201_CREATED)

        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    def _create_journal_post_data(self, request_data, entry_type):
        data = {
            'title': request_data.get('title'),
            'description': request_data.get('description'),
            'type': entry_type,
        }
        if entry_type == JournalTypes.STUDENT_POST:
            data['student'] = self.gen_user.student.id
            data['skill'] = request_data.get('skill')
        elif entry_type == JournalTypes.TEACHER_FEEDBACK:
            data['student'] = self.request.query_params.get('student_id')
            data['teacher'] = self.gen_user.teacher.id

        return data

    def partial_update(self, request, *args, **kwargs):
        journal_post = self.get_object()

        if self.gen_user.is_student:
            success_message = SuccessMessages.STUDENT_POST_UPDATED
            error_message = ErrorMessages.STUDENT_POST_UPDATE_FAILED
        elif self.gen_user.is_teacher:
            success_message = SuccessMessages.TEACHER_FEEDBACK_UPDATED
            error_message = ErrorMessages.TEACHER_FEEDBACK_UPDATE_FAILED

        serializer = self.get_serializer(journal_post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(success_message, status=status.HTTP_200_OK)

        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            if self.gen_user.is_student:
                return StudentPostSerializer
            elif self.gen_user.is_teacher:
                return TeacherFeedbackSerializer

        return JournalListSerializer
