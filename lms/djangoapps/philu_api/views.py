"""
restAPI Views
"""
import logging
import requests

from datetime import datetime
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView

from lms.djangoapps.onboarding.forms import RegModelForm
from lms.djangoapps.onboarding.helpers import get_country_iso
from student.models import User

from lms.djangoapps.onboarding.models import Organization, UserExtendedProfile
from lms.djangoapps.philu_api.helpers import get_encoded_token

log = logging.getLogger("edx.philu_api")


class UpdateCommunityProfile(APIView):
    """ Retrieve order details. """

    def post(self, request):
        """ Update provided information in openEdx received from nodeBB client """

        username = request.GET.get('username')
        email = request.GET.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'message': "User does not exist for provided username"}, status=status.HTTP_400_BAD_REQUEST)

        id = user.id        

        token = request.META["HTTP_X_CSRFTOKEN"]
        if not token == get_encoded_token(username, email, id):
            return JsonResponse({"message": "Invalid Session token"}, status=status.HTTP_400_BAD_REQUEST)
        
        extended_profile = user.extended_profile
        userprofile = user.profile

        data = request.data

        try:
            first_name = data.get('first_name', user.first_name)
            last_name = data.get('last_name', user.last_name)
            birthday = data.get('birthday')

            about_me = data.get('aboutme', userprofile.bio)
            language = data.get('language', userprofile.language)
            city = data.get('city_of_residence', userprofile.city)
            country = data.get('country_of_residence', userprofile.country)

            city_of_employment = data.get('city_of_employment', extended_profile.city_of_employment)
            country_of_employment = data.get('country_of_employment', extended_profile.country_of_employment if
            extended_profile.country_of_employment else "")

            if birthday:
                birthday_year = birthday.split("/")[2]
            else:
                birthday_year = userprofile.year_of_birth

            user.first_name = first_name
            user.last_name = last_name

            user.profile.bio = about_me
            userprofile.city = city
            userprofile.country = get_country_iso(country)
            userprofile.language = language

            extended_profile.city_of_employment = city_of_employment
            extended_profile.country_of_employment = get_country_iso(country_of_employment)

            if birthday:
                userprofile.year_of_birth = int(birthday_year)

            user.save()
            userprofile.save()
            extended_profile.save()

            return JsonResponse({"message": "user info updated successfully"}, status=status.HTTP_200_OK)
        except Exception as ex:
            return JsonResponse({"message": str(ex.args)}, status=status.HTTP_400_BAD_REQUEST)


def get_user_chat(request):
    """ Get recent chats of the user from NodeBB """

    chat_endpoint = settings.NODEBB_ENDPOINT + '/api/v2/users/chats'
    username = request.user.username
    headers = {'Authorization': 'Bearer ' + settings.NODEBB_MASTER_TOKEN}
    response = requests.post(chat_endpoint,
        data={'_uid': 1, 'username': username},
        headers=headers)
    return JsonResponse(response.json())

def mark_user_chat_read(request):
    """ Mark all chats of the user as read """

    chat_endpoint = settings.NODEBB_ENDPOINT + '/api/v2/users/chats'
    username = request.user.username
    headers = {'Authorization': 'Bearer ' + settings.NODEBB_MASTER_TOKEN}
    response = requests.patch(chat_endpoint,
        data={'_uid': 1, 'username': username},
        headers=headers)
    return JsonResponse(response.json())
