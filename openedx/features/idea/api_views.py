"""
API views for Idea app
"""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from openedx.features.idea.models import Idea


class FavoriteAPIView(APIView):
    """
    FavoriteAPIView is used to toggle favorite idea for the user
    """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, idea_id):
        """
        Update the favorite status for idea and return it.

        Arguments:
            request (HttpRequest): Request object for post call
            idea_id (int): Idea id whose status needs to be toggled

        Returns:
            JsonResponse: JsonResponse object contains message and favorite status
        """
        response = {'message': 'Idea is added to favorites', 'is_idea_favorite': True}
        toggle_status = status.HTTP_201_CREATED
        user = request.user
        idea = get_object_or_404(Idea, pk=idea_id)
        toggle_favorite_status = idea.toggle_favorite(user)

        if not toggle_favorite_status:
            response['is_idea_favorite'] = False
            response['message'] = 'Idea is removed from favorites'
            toggle_status = status.HTTP_200_OK

        response['favorite_count'] = idea.favorites.count()
        return JsonResponse(response, status=toggle_status)
