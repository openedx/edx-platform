"""
restAPI Views
"""
import json
from django.views.decorators.http import require_POST
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from student.models import User


THREADS_PER_PAGE = 20
INLINE_THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2
log = logging.getLogger("edx.philu_api")



@require_POST
@login_required
def update_community_profile_update(request):
    """
    Update provided information in openEdx received from nodeBB client
    """

    user = User.objects.get(username=request.GET.get('username'))
    data = json.loads(request.body)
    extended_profile = user.extended_profile
    user_info_survey = user.user_info_survey

    try:
        first_name = data.get('first_name', extended_profile.first_name)
        last_name = data.get('last_name', extended_profile.last_name)
        bio = data.get('bio', user.profile.bio)

        city = data.get('city', user_info_survey.city_of_residence)
        country = data.get('country', user_info_survey.country_of_residence)
        dob = data.get('dob', user_info_survey.dob)

        extended_profile.firs_name = first_name
        extended_profile.firs_name = last_name
        user.profile.bio = bio

        user_info_survey.city_of_residence = city
        user_info_survey.country_of_residence = country

        user_info_survey.dob = dob

        extended_profile.save()
        user_info_survey.save()

        return JsonResponse({
            "message": "user info updated successfully",
            "success": True
        })

    except Exception as ex:
        return JsonResponse({
            "message": str(ex.args),
            "success": False
        })