from django.middleware import csrf
from django.utils.decorators import method_decorator

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import GenUser, Character
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
            gen_user = GenUser.objects.get(user=self.request.user)
        except GenUser.DoesNotExist:
            return Response(ErrorMessages.INTERNAL_SERVER, status=status.HTTP_400_BAD_REQUEST)

        user_info = {
            'id': self.request.user.id,
            'name': self.request.user.profile.name,
            'username': self.request.user.username,
            'csrf_token': csrf.get_token(self.request),
            'role': gen_user.role
        }
        if gen_user.is_student:
            user_info.update({'onboarded': gen_user.student.onboarded})

        return Response(status=status.HTTP_200_OK, data=user_info)


class CharacterViewSet(viewsets.ModelViewSet):
    """
    Viewset for character APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated & IsStudent]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()

    @action(detail=True, methods=['post'])
    def select_character(self, request, pk=None):  # pylint: disable=unused-argument
        """
        select character at the time of onboarding or changing character from
        the profile
        """
        character = self.get_object()
        genuser = GenUser.objects.get(user=self.request.user)
        genuser.student.character = character
        if request.data.get("onboarded") and not genuser.student.onboarded:
            genuser.student.onboarded = True

        genuser.student.save()
        return Response(SuccessMessage.CHARACTER_SELECTED, status=status.HTTP_204_NO_CONTENT)
