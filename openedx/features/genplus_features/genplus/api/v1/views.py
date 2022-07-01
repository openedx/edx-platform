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
from .serializers import CharacterSerializer, ClassSerializer, FavoriteClassSerializer
from .permissions import IsStudent, IsTeacher
from openedx.features.genplus_features.genplus.display_messages import SuccessMessages, ErrorMessages


class UserInfo(views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        try:
            gen_user = GenUser.objects.select_related('user', 'school').get(user=self.request.user)
        except GenUser.DoesNotExist:
            return Response(ErrorMessages.INTERNAL_SERVER, status=status.HTTP_400_BAD_REQUEST)

        user_info = {
            'id': self.request.user.id,
            'name': self.request.user.profile.name,
            'username': self.request.user.username,
            'csrf_token': csrf.get_token(self.request),
            'role': gen_user.role,
            'first_name': gen_user.user.first_name,
            'last_name': gen_user.user.last_name,
            'email': gen_user.user.email,
            'school': gen_user.school.name,
            'on_board': '',
            'character_id': '',
            'profile_image': '',
        }

        if gen_user.is_student:
            student = {
                'on_board': gen_user.student.onboarded,
                'character_id': gen_user.student.character.id
                                if gen_user.student.character else None,
                'profile_image': gen_user.student.character.profile_pic.url
                                 if gen_user.student.character else None
            }
            user_info.update(student)
        if gen_user.is_teacher:
            teacher = {
                'profile_image': gen_user.teacher.profile_image.url
                                 if gen_user.teacher.profile_image else None
            }
            user_info.update(teacher)

        return Response(status=status.HTTP_200_OK, data=user_info)

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        update user's profile image
        """
        try:
            gen_user = GenUser.objects.get(user=self.request.user)
            if gen_user.is_teacher:
                image = self.request.data.get('image', None)
                if not image:
                    raise ValueError('image field was empty')
                teacher = Teacher.objects.get(gen_user=gen_user)
                teacher.profile_image = image
                teacher.save()

            if gen_user.is_student:
                character = self.request.data.get('character', None)
                if not character:
                    raise ValueError('character field was empty')
                new_character = Character.objects.get(id=int(character))
                student = Student.objects.get(gen_user=gen_user)
                student.character  = new_character
                student.save()

            return Response(SuccessMessages.PROFILE_IMAGE_UPDATED, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)



class CharacterViewSet(viewsets.ModelViewSet):
    """
    Viewset for character APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()

    @action(detail=True, methods=['post'])
    def select_character(self, request, pk=None):  # pylint: disable=unused-argument
        """
        select character at the time of onboarding or changing character from
        the profile
        """
        character = self.get_object()
        gen_user = GenUser.objects.get(user=self.request.user)
        gen_user.student.character = character
        if request.data.get("onboarded") and not gen_user.student.onboarded:
            gen_user.student.onboarded = True

        gen_user.student.save()
        return Response(SuccessMessages.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)


class ClassViewSet(viewsets.ModelViewSet):
    """
    Viewset for class APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer
    lookup_field = 'group_id'

    def get_queryset(self):
        return Class.visible_objects.filter(school=self.request.user.genuser.school)

    def list(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        gen_user = self.request.user.gen_user
        favourite_classes = gen_user.teacher.favourite_classes.all()
        favourite_classes_serializer = self.get_serializer(favourite_classes, many=True)
        class_queryset = self.filter_queryset(self.get_queryset())
        class_serializer = self.get_serializer(
            class_queryset.exclude(group_id__in=gen_user.teacher.favourite_classes.values('group_id', )),
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
        rm_class = self.get_object()
        genuser = GenUser.objects.get(user=self.request.user)
        if data['action'] == 'add':
            genuser.teacher.favourite_classes.add(rm_class)
            return Response(SuccessMessages.CLASS_ADDED_TO_FAVORITES.format(class_name=rm_class.name),
                            status=status.HTTP_204_NO_CONTENT)
        else:
            genuser.teacher.favourite_classes.remove(rm_class)
            return Response(SuccessMessages.CLASS_REMOVED_FROM_FAVORITES.format(class_name=rm_class.name),
                            status=status.HTTP_204_NO_CONTENT)
