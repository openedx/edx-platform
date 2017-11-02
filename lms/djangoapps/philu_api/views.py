"""
restAPI Views
"""
import logging

from datetime import datetime
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from student.models import User

from lms.djangoapps.onboarding_survey.models import Organization, ExtendedProfile
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
        user_info_survey = user.user_info_survey

        data = request.data

        try:
            first_name = data.get('first_name', extended_profile.first_name)
            last_name = data.get('last_name', extended_profile.last_name)
            about_me = data.get('aboutme', user.profile.bio)
            organization = data.get('organization')
            if organization:
                organization, is_created = Organization.objects.get_or_create(name=organization)

                if organization != extended_profile.organization:
                    is_poc_value, is_poc_label = ExtendedProfile.POC_CHOICES[0]
                    extended_profile.org_admin_email = ""
                    extended_profile.is_poc = is_poc_value
                    extended_profile.organization = organization

            city_of_residence = data.get('city_of_residence', user_info_survey.city_of_residence)
            country_of_residence = data.get('country_of_residence', user_info_survey.country_of_residence)
            city_of_employment = data.get('city_of_employment', user_info_survey.city_of_employment)
            country_of_employment = data.get('country_of_employment', user_info_survey.country_of_employment)

            language = data.get('language', user_info_survey.language)

            birthday = data.get('birthday')
            if birthday:
                birthday_year = birthday.split("/")[2]
            else:
                birthday_year = user_info_survey.year_of_birth

            extended_profile.first_name = first_name
            extended_profile.last_name = last_name
            user.profile.bio = about_me
            user_info_survey.city_of_residence = city_of_residence
            user_info_survey.country_of_residence = country_of_residence
            user_info_survey.city_of_employment = city_of_employment
            user_info_survey.country_of_employment = country_of_employment
            user_info_survey.language = language

            if birthday:
                user_info_survey.year_of_birth = birthday_year

            extended_profile.save()
            user_info_survey.save()

            return JsonResponse({"message": "user info updated successfully"}, status=status.HTTP_200_OK)
        except Exception as ex:
            return JsonResponse({"message": str(ex.args)}, status=status.HTTP_400_BAD_REQUEST)

