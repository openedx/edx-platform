from django.middleware import csrf
from django.utils.decorators import method_decorator

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Character, Teacher, Student
from .serializers import CharacterSerializer
from .permissions import IsStudent
from .messages import SuccessMessage, ErrorMessages


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

            return Response(SuccessMessage.PROFILE_IMAGE_UPDATED, status=status.HTTP_200_OK)
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
        return Response(SuccessMessage.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)
