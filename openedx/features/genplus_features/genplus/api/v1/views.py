from django.middleware import csrf
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Character, Class, Teacher, Student
from .serializers import CharacterSerializer, ClassSerializer, FavoriteClassSerializer, UserInfoSerializer
from .permissions import IsStudent, IsTeacher
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages, ErrorMessages
from .mixins import GenzMixin


class UserInfo(GenzMixin, views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        user_info = UserInfoSerializer(self.request.user, context={
            'request': self.request,
            'gen_user': self.gen_user
        })

        return Response(status=status.HTTP_200_OK, data=user_info.data)

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
        favourite_classes = self.gen_user.teacher.favourite_classes.all()
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
        if data['action'] == 'add':
            teacher.favourite_classes.add(gen_class)
            return Response(SuccessMessages.CLASS_ADDED_TO_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)
        else:
            teacher.favourite_classes.remove(gen_class)
            return Response(SuccessMessages.CLASS_REMOVED_FROM_FAVORITES.format(class_name=gen_class.name),
                            status=status.HTTP_204_NO_CONTENT)
