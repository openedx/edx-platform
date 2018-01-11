import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from rest_framework import status

from lms.djangoapps.oef.helpers import *


@login_required
def oef_dashboard(request):
    """
    View for OEF dashboard

    """
    user_surveys = OrganizationOefScore.objects.filter(user_id=request.user.id)
    surveys = []
    user_survey_status = get_user_survey_status(request.user, create_new_survey=False)
    for survey in user_surveys:
        surveys.append({
            'id': survey.id,
            'started_on': survey.start_date.strftime('%m/%d/%Y'),
            'completed_on': survey.finish_date.strftime('%m/%d/%Y') if survey.finish_date else '',
            'status': 'Draft' if not survey.finish_date else 'Finished'
        })

    return render(request, 'oef/oef-org.html', {'surveys': surveys, 'error': user_survey_status['error']})


@login_required
def oef_instructions(request):
    """
    View for instructions page of OEF
    """
    survey_info = get_user_survey_status(request.user, create_new_survey=False)
    oef_url = reverse('oef_dashboard') if survey_info['error'] else reverse('oef_survey')
    return render(request, 'oef/oef-instructional.html', {'oef_url': oef_url})


@login_required
def get_survey_by_id(request, user_survey_id):
    """
    Get a particular survey by its id
    """

    uos = OrganizationOefScore.objects.get(id=int(user_survey_id), user_id=request.user.id)
    survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    topics = get_survey_topics(uos, survey.id)
    levels = get_option_levels()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "is_completed": bool(uos.finish_date),
                                                   "topics": topics,
                                                   "levels": levels
                                                   })


@login_required
def fetch_survey(request):
    """
    Fetch appropriate survey for the user

    """
    survey_info = get_user_survey_status(request.user)
    if not survey_info['survey']:
        return redirect(reverse('oef_dashboard'))

    uos = get_user_survey(request.user, survey_info['survey'])
    survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    topics = get_survey_topics(uos, survey.id)
    levels = get_option_levels()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "topics": topics,
                                                   "levels": levels,
                                                   'is_completed': False,
                                                   })


@login_required
def save_answer(request):
    """
    Save answers submitted by user
    """
    data = json.loads(request.body)
    uos = OrganizationOefScore.objects.filter(user_id=request.user.id).latest('start_date')

    for answer_data in data['answers']:
        setattr(uos, answer_data['score_name'], int(float(answer_data['answer_id'])))

    if data['is_complete']:
        uos.finish_date = datetime.date.today()
    uos.save()

    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
