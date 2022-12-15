from django.middleware import csrf
from django.http import Http404
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework import mixins
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_multiple_model.mixins import FlatMultipleModelMixin

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import (
    GenUser, Character, Class, Teacher, Student, JournalPost, Skill
)
from openedx.features.genplus_features.genplus.constants import JournalTypes, EmailTypes
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.genplus_badges.api.v1.serializers import JournalBoosterBadgeSerializer
from openedx.features.genplus_features.genplus_badges.models import BoosterBadgeAward
from django.views.decorators.debug import sensitive_post_parameters
from .serializers import (
    CharacterSerializer,
    ClassListSerializer,
    ClassSummarySerializer,
    FavoriteClassSerializer,
    UserInfoSerializer,
    JournalListSerializer,
    StudentPostSerializer,
    TeacherFeedbackSerializer,
    SkillSerializer,
    ContactSerailizer,
    ChangePasswordByTeacherSerializer,
    ChangePasswordSerializer
)
from .permissions import IsStudent, IsTeacher, IsStudentOrTeacher, IsGenUser, FromPrivateSchool
from .mixins import GenzMixin
from .pagination import JournalListPagination


sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password', 'old_password', 'new_password1', 'new_password2'
    )
)


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

        student.save(update_fields=['onboarded', 'character'])
        return Response(SuccessMessages.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)


class ClassViewSet(GenzMixin, viewsets.ModelViewSet):
    """
    Viewset for class APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Class.visible_objects.filter(school=self.school)

    def list(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        favorite_classes = self.gen_user.teacher.favorite_classes.all()
        favorite_classes_serializer = self.get_serializer(favorite_classes, many=True)
        class_queryset = self.filter_queryset(self.get_queryset())
        class_serializer = self.get_serializer(
            class_queryset.exclude(group_id__in=favorite_classes.values('group_id', )),
            many=True)
        data = {
            'favourite_classes': favorite_classes_serializer.data,
            'classes': class_serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def add_my_class(self, request, pk=None):  # pylint: disable=unused-argument
        """
        add classes to the my classes for teacher
        """
        serializer = FavoriteClassSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        gen_class = self.get_object()
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        if data['action'] == 'add':
            teacher.favorite_classes.add(gen_class)
            return Response(SuccessMessages.CLASS_ADDED_TO_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)
        else:
            teacher.favorite_classes.remove(gen_class)
            return Response(SuccessMessages.CLASS_REMOVED_FROM_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in ['list']:
            return ClassListSerializer

        return ClassSummarySerializer

class JournalViewSet(GenzMixin, FlatMultipleModelMixin, viewsets.ModelViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    queryset = JournalPost.objects.none()
    sorting_field = 'created'
    pagination_class = JournalListPagination
    sort_descending = True

    def _journal_entry_filter(self, queryset, request, *args, **kwargs):
        query_params = self.request.query_params
        skill_id = query_params.get('skill_id')
        search = query_params.get('search', '')
        if skill_id:
            queryset = queryset.filter(skill__id=skill_id)
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def _booster_badge_filter(self, queryset, request, *args, **kwargs):
        query_params = self.request.query_params
        skill_id = query_params.get('skill_id')
        if skill_id:
            return BoosterBadgeAward.objects.none()
        search = query_params.get('search', '')
        queryset = queryset.filter(feedback__icontains=search)
        return queryset

    def _rename_entry_type(self, results):
        for i, entry in enumerate(results):
            if entry['type'] == 'JournalPost':
                results[i]['type'] = results[i]['journal_type']
        return results

    def sort_results(self, results):
        # Sorting on the basis of a common field in all the objects.
        results.sort(key=lambda obj: obj['created'], reverse=True)
        return results

    def get_querylist(self):
        query_params = self.request.query_params
        journal_posts = JournalPost.objects.select_related('student', 'teacher', 'skill')

        if self.gen_user.is_student:
            student = self.gen_user.student
            journal_posts = journal_posts.filter(student=student)
            booster_badges = BoosterBadgeAward.objects.filter(user=self.gen_user.user)
        else:
            student_id = query_params.get('student_id')
            student = get_object_or_404(Student, pk=student_id)
            journal_posts = journal_posts.filter(student=student)
            booster_badges = BoosterBadgeAward.objects.filter(user__gen_user=student.gen_user)

        return [
            {
                'queryset': journal_posts,
                'serializer_class': JournalListSerializer,
                'filter_fn': self._journal_entry_filter
            },
            {
                'queryset': booster_badges,
                'serializer_class': JournalBoosterBadgeSerializer,
                'filter_fn': self._booster_badge_filter
            }
        ]

    def list(self, request, *args, **kwargs):
        response = super(FlatMultipleModelMixin, self).list(request, args, kwargs)
        response.data['results'] = self._rename_entry_type(response.data['results'])
        querylist = self.get_querylist()
        queryset = querylist[0]['queryset']
        skills_qs = Skill.objects.filter(pk__in=queryset.values_list('skill', flat=True))
        response.data['skills'] = SkillSerializer(skills_qs, many=True).data
        return response


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

    def _create_journal_post_data(self, request_data, journal_type):
        data = {
            'title': request_data.get('title'),
            'description': request_data.get('description'),
            'journal_type': journal_type,
        }
        if journal_type == JournalTypes.STUDENT_POST:
            data['student'] = self.gen_user.student.id
            data['skill'] = request_data.get('skill')
        elif journal_type == JournalTypes.TEACHER_FEEDBACK:
            data['student'] = request_data.get('student_id')
            data['teacher'] = self.gen_user.teacher.id

        return data

    def partial_update(self, request, pk=None, *args, **kwargs):
        journal_post = get_object_or_404(JournalPost, pk=pk)

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


class SkillViewSet(GenzMixin, viewsets.ReadOnlyModelViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudentOrTeacher]
    serializer_class = SkillSerializer
    queryset = Skill.objects.all()
    pagination_class = None
    ordering = ['name']


class ContactAPIView(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, *args, **kwargs):
        email_data = {
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'to_email': settings.CONTACT_EMAIL,
            'subject': EmailTypes.MISSING_CLASS_EMAIL,
        }
        serializer = ContactSerailizer(data=email_data)
        message = request.data.get('message', '')

        if serializer.is_valid() and message:
            record = serializer.save()
            subject = f'{record.subject} ref:{record.email_reference}'
            email = request.user.email

            data = {
                'name': request.user.profile.name,
                'school': request.user.gen_user.school.name,
                'message': message,
            }

            plain_message = get_template('genplus/contact_us_email.txt')
            html_message  = get_template('genplus/contact_us_email.html')
            text_content = plain_message.render(data)
            html_content = html_message.render(data)

            msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_EMAIL])
            msg.cc = [email]
            msg.attach_alternative(html_content, "text/html")

            msg_status = msg.send(fail_silently=True)

            if (msg_status > 0):
                return Response({"success": "Sent"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordByTeacherView(GenzMixin, views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher, FromPrivateSchool]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordByTeacherSerializer(data=request.data)
        users_list = []
        if serializer.is_valid():
            students = serializer.data['students']
            password = serializer.data['password']
            for student in Student.objects.filter(id__in=students):
                if student.gen_user.from_private_school:
                    user = student.gen_user.user
                    user.set_password(password)
                    user.save()
                    users_list.append(user.email)
            return Response({"message": SuccessMessages.PASSWORD_CHANGED_BY_TEACHER.format(users=','.join(users_list))},
                            status=status.HTTP_200_OK)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(GenzMixin, generics.GenericAPIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, FromPrivateSchool]
    serializer_class = ChangePasswordSerializer

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "New password has been saved."})
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
