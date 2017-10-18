"""
restAPI Views
"""
import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from student.models import User

from lms.djangoapps.philu_api.helpers import get_encoded_token

log = logging.getLogger("edx.philu_api")


class UpdateCommunityProfile(APIView):
    """ Retrieve order details. """

    def post(self, request):
        """ Update provided information in openEdx received from nodeBB client """

        username = request.GET.get('username')
        email = request.GET.get('email')

        token = request.META["HTTP_X_CSRFTOKEN"]
        if not token == get_encoded_token(username, email):
            return JsonResponse({"message": "Invalid Session token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'message': "User does not exist for provided username"}, status=status.HTTP_400_BAD_REQUEST)

        extended_profile = user.extended_profile
        user_info_survey = user.user_info_survey

        data = request.data

        try:
            first_name = data.get('first_name', extended_profile.first_name)
            last_name = data.get('last_name', extended_profile.last_name)
            bio = data.get('bio', user.profile.bio)

            city = data.get('city', user_info_survey.city_of_residence)
            country = data.get('country', user_info_survey.country_of_residence)
            dob = data.get('dob', user_info_survey.dob)

            extended_profile.first_name = first_name
            extended_profile.last_name = last_name
            user.profile.bio = bio

            user_info_survey.city_of_residence = city
            user_info_survey.country_of_residence = country

            user_info_survey.dob = dob

            extended_profile.save()
            user_info_survey.save()

            return JsonResponse({"message": "user info updated successfully"}, status=status.HTTP_200_OK)
        except Exception as ex:
            return JsonResponse({"message": str(ex.args)}, status=status.HTTP_400_BAD_REQUEST)

