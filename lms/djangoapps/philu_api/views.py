"""
restAPI Views
"""

from functools import wraps
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from student.models import User


THREADS_PER_PAGE = 20
INLINE_THREADS_PER_PAGE = 20
PAGES_NEARBY_DELTA = 2
log = logging.getLogger("edx.philu_api")



# @require_POST
# @login_required
def update_community_profile_update(request):
    """
    Update provided information in openEdx received from nodeBB client
    """

    user = User.objects.get(username=request.GET.get('username'))
    data = request.POST
    extended_profile = user.extended_profile
    user_info_survey = user.user_info_survey

    try:
        first_name = data.get('firs_name')
        last_name = data.get('last_name')
        bio = data.get('bio')

        city = data.get('city')
        country = data.get('country')
        dob = data.get('dob')

        if first_name:
            extended_profile.firs_name = data.first_name
        if last_name:
            extended_profile.firs_name = data.last_name
        if bio:
            user.profile.bio = bio

        if city and country:
            user_info_survey.location = "{city}, {country}".format(city=city, country=country)

        if dob:
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

