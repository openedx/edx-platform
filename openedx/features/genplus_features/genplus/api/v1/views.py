from django.middleware import csrf
from django.utils.decorators import method_decorator

from rest_framework import generics, status, views, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.features.genplus_features.genplus.models import GenUser, Character
from .serializers import CharacterSerializer
from .permissions import IsStudent
from .messages import SuccessMessage, ErrorMessages


class UserInfo(views.APIView):
    """
    API for genplus user information
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        get user's basic info
        """
        try:
            gen_user = GenUser.objects.get(user=self.request.user)
        except GenUser.DoesNotExist:
            gen_user = None

        user_info = {
            'id': self.request.user.id,
            'name': self.request.user.profile.name,
            'username': self.request.user.username,
            'csrf_token': csrf.get_token(self.request),
            'role': gen_user.role
        }
        if gen_user.role == GenUser.STUDENT:
            user_info.update({'on_board': gen_user.student.on_board})
        return Response(status=status.HTTP_200_OK, data=user_info)


class CharacterView(generics.ListAPIView):
    """
    API for characters list
    """
    permission_classes = [IsAuthenticated & IsStudent]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()


class StudentOnBoard(views.APIView):
    """
    API for on-boarding the student
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated & IsStudent]

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        onboard user and bind the character
        """
        try:
            character = Character.objects.get(pk=self.request.data['character_id'])
            genuser = GenUser.objects.get(user_id=self.request.user.id)
            genuser.student.character = character
            genuser.student.save()
            return Response(SuccessMessage.ON_BOARD_SUCCESS, status=status.HTTP_204_NO_CONTENT)
        except Character.DoesNotExist:
            return Response(ErrorMessages.INTERNAL_SERVER, status=status.HTTP_400_BAD_REQUEST)



