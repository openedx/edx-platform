import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from rest_framework import status

from lms.djangoapps.oef.decorators import can_take_oef
from lms.djangoapps.oef.helpers import *
from lms.djangoapps.onboarding.models import Organization
from lms.djangoapps.onboarding.helpers import oef_eligible_first_learner


@login_required
def oef_dashboard(request):
    """
    View for OEF dashboard

    """
    surveys = []
    user_survey_status = get_user_survey_status(request.user, create_new_survey=False)
    user_extended_profile = request.user.extended_profile
    is_first_user = user_extended_profile.is_first_signup_in_org if user_extended_profile.organization else False
    user_surveys = OrganizationOefScore.objects.filter(org=user_extended_profile.organization)

    context = {
        'user_has_organization': bool(user_extended_profile.organization),
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'is_poc': user_extended_profile.is_organization_admin,
        'is_first_user': is_first_user,
        'first_learner_submitted_oef': is_first_user and user_extended_profile.has_submitted_oef()
    }

    for survey in user_surveys:
        surveys.append({
            'id': survey.id,
            'started_on': survey.start_date.strftime('%m/%d/%Y'),
            'completed_on': survey.finish_date.strftime('%m/%d/%Y') if survey.finish_date else '',
            'modified': survey.modified.strftime('%m/%d/%Y'),
            'status': 'Draft' if not survey.finish_date else 'Finished'
        })

    context.update({'surveys': surveys, 'error': user_survey_status['error']})

    return render(request, 'oef/oef-org.html', context)


@login_required
@can_take_oef
def oef_instructions(request):
    """
    View for instructions page of OEF
    """
    survey_info = get_user_survey_status(request.user, create_new_survey=False)
    oef_url = reverse('oef_dashboard') if survey_info['error'] else reverse('oef_survey')
    return render(request, 'oef/oef-instructional.html', {'oef_url': oef_url})


@login_required
@can_take_oef
def get_survey_by_id(request, user_survey_id):
    """
    Get a particular survey by its id
    """
    organization = request.user.extended_profile.organization

    uos = OrganizationOefScore.objects.get(id=int(user_survey_id), org=organization)
    survey = OefSurvey.objects.filter(is_enabled=True).latest('created')
    topics = get_survey_topics(uos, survey.id)
    levels = get_option_levels()
    return render(request, 'oef/oef_survey.html', {"survey_id": survey.id,
                                                   "is_completed": bool(uos.finish_date),
                                                   "description": survey.description,
                                                   "topics": topics,
                                                   "instructions": get_oef_instructions(),
                                                   "levels": levels,
                                                   'organization': organization.label,
                                                   'date': uos.modified.strftime('%m/%d/%Y')
                                                   })


@login_required
@can_take_oef
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
                                                   "description": survey.description,
                                                   "topics": topics,
                                                   "levels": levels,
                                                   'is_completed': False,
                                                   "instructions": get_oef_instructions(),
                                                   'organization': request.user.extended_profile.organization.label,
                                                   'date': uos.start_date.strftime('%m/%d/%Y')
                                                   })


@login_required
@can_take_oef
def save_answer(request):
    """
    Save answers submitted by user
    """
    data = json.loads(request.body)
    organization = request.user.extended_profile.organization
    uos = OrganizationOefScore.objects.filter(org=organization).latest('start_date')

    for answer_data in data['answers']:
        setattr(uos, answer_data['score_name'], int(float(answer_data['answer_id'])))

    if data['is_complete']:
        uos.finish_date = datetime.date.today()
    uos.save()

    return JsonResponse({
        'status': 'success'
    }, status=status.HTTP_201_CREATED)
