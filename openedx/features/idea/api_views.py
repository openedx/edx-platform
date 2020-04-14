from django.http import JsonResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from openedx.features.idea.models import Idea


class FavoriteAPIView(APIView):
    """
    FavoriteAPIView is used t toggle favorite idea for the user
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request, idea_id):
        response = dict(message='User is added to favorites')
        http_status = status.HTTP_201_CREATED
        user = request.user
        idea = Idea.objects.get(pk=idea_id)
        if not idea.toggle_favorite(user):
            response['message'] = 'User is removed from favorites'
            http_status = status.HTTP_200_OK

        return JsonResponse(response, status=http_status)
