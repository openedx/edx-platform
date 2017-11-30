import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from rest_framework import status

from lms.djangoapps.oef.helpers import *


@login_required
def oef_dashboard(request):
    user_surveys = UserOefSurvey.objects.filter(user_id=request.user.id)
    surveys = []
    for survey in user_surveys:
        surveys.append({
            'id': survey.id,
            'started_on': survey.started_on.strftime('%m/%d/%Y'),
            'completed_on': survey.completed_on.strftime('%m/%d/%Y') if survey.completed_on else '',
            'status': survey.status
        })

    return render(request, 'oef/oef-org.html', {'surveys': surveys})


@login_required
def oef_instructions(request):
    survey_info = get_user_survey_status(request.user, create_new_survey=False)
    if survey_info['error']:
        return redirect(reverse('courses'))
    return render(request, 'oef/oef-instructional.html', {})


@login_required
def get_survey_by_id(request, user_survey_id):
    uos = UserOefSurvey.objects.get(id=int(user_survey_id), user_id=request.user.id)
    survey = uos.survey
    topics = get_survey_topics(uos, survey.id)
    levels = get_option_levels()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "is_completed": uos.status == 'completed',
                                                   "topics": topics,
                                                   "levels": levels
                                                   })


@login_required
def fetch_survey(request):
    survey_info = get_user_survey_status(request.user)
    if not survey_info['survey']:
        return redirect(reverse('recommendations'))

    uos = get_user_survey(request.user, survey_info['survey'])
    survey = uos.survey
    topics = get_survey_topics(uos, survey.id)
    levles = get_option_levels()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "topics": topics,
                                                   "levels": levles,
                                                   'is_completed': uos.status == 'completed',
                                                   })


@login_required
def save_answer(request):
    data = json.loads(request.body)
    survey_id = int(data['survey_id'])
    uos = UserOefSurvey.objects.get(survey_id=survey_id, user_id=request.user.id)

    for answer_data in data['answers']:
        question_id = int(answer_data['topic_id'])

        answer = get_answer(uos, question_id) or create_answer(uos, answer_data)
        answer.selected_option = get_option(float(answer_data['answer_id']))
        answer.save()

    check_if_complete(uos, len(data['answers']))
    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
