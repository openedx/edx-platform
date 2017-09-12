"""
Views for on-boarding app.
"""
import json
import os

from path import Path as path

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from lms.djangoapps.onboarding_survey.models import (
    UserInfoSurvey,
    InterestsSurvey,
    OrganizationSurvey
)

from onboarding_survey import forms


def get_un_submitted_surveys(user):
    """
    Get the info about the un-submitted forms
    """
    un_submitted_surveys = {}
    try:
        user.user_info_survey
    except Exception:
        un_submitted_surveys['user_info'] = True

    try:
        user.interest_survey
    except Exception:
        un_submitted_surveys['interests'] = True

    try:
        user.organization_survey
    except Exception:
        un_submitted_surveys['organization'] = True

    if un_submitted_surveys.get('user_info') and un_submitted_surveys.get('interests') and un_submitted_surveys.get('organization'):
        un_submitted_surveys['user_info'] = False

    elif un_submitted_surveys.get('interests') and un_submitted_surveys.get('organization'):
        un_submitted_surveys['user_info'] = False
        un_submitted_surveys['interests'] = False

    else:
        un_submitted_surveys['user_info'] = False
        un_submitted_surveys['interests'] = False
        un_submitted_surveys['organization'] = False

    return un_submitted_surveys

@login_required
def user_info(request):
    """
    The view to handle user info survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request data and
    is then saved. After saving the form, user is redirected to the
    next survey namely, interests survey.
    """

    if request.method == 'POST':
        try:
            form = forms.UserInfoModelForm(request.POST, instance=request.user.user_info_survey)
            if form.is_valid():
                form.save()
                return redirect(reverse('interests'))

        except UserInfoSurvey.DoesNotExist:
            form = forms.UserInfoModelForm(request.POST)
            if form.is_valid():
                user_info_survey = form.save()
                user_info_survey.user = request.user
                user_info_survey.save()
                return redirect(reverse('interests'))

    else:
        user_info_instance = UserInfoSurvey.objects.filter(user=request.user).first()
        if user_info_instance:
            if user_info_instance.dob:
                form = forms.UserInfoModelForm(
                    instance=user_info_instance, initial={'dob': user_info_instance.dob.strftime("%m/%d/%y")}
                )
            else:
                form = forms.UserInfoModelForm(
                    instance=user_info_instance
                )
        else:
            form = forms.UserInfoModelForm()

    context = {'form': form}
    user = request.user
    context.update(get_un_submitted_surveys(user))

    return render(request, 'tell_us_more_survey.html', context)


@login_required
def interests(request):
    """
    The view to handle interests survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to the next survey
    namely, organization survey.

    """
    if request.method == 'POST':
        try:
            form = forms.InterestModelForm(request.POST, instance=request.user.interest_survey)
            if form.is_valid():
                form.save()
                return redirect(reverse('organization'))

        except InterestsSurvey.DoesNotExist:
            form = forms.InterestModelForm(request.POST)
            if form.is_valid():
                interest_survey = form.save()
                interest_survey.user = request.user
                interest_survey.save()
                return redirect(reverse('organization'))

    else:
        user_interest_survey_instance = InterestsSurvey.objects.filter(user=request.user).first()
        if user_interest_survey_instance:
            form = forms.InterestModelForm(label_suffix="", instance=user_interest_survey_instance)
        else:
            form = forms.InterestModelForm(label_suffix="")

    context = {'form': form}

    user = request.user
    context.update(get_un_submitted_surveys(user))

    return render(request, 'interests_survey.html', context)


def mark_partner_network(organization_survey):
    """
    Marks partner as affiliated if not already.
    """
    partner_network = organization_survey.partner_network
    if partner_network:
        if not partner_network.is_partner_affiliated:
            partner_network.is_partner_affiliated = True
            partner_network.save()


@login_required
def organization(request):
    """
    The view to handle organization survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to dashboard.
    """
    if request.method == 'POST':

        try:
            form = forms.OrganizationInfoModelForm(request.POST, instance=request.user.organization_survey)
            if form.is_valid():
                organization_survey = form.save()
                mark_partner_network(organization_survey)
                return redirect(reverse('dashboard'))

        except OrganizationSurvey.DoesNotExist:
            form = forms.OrganizationInfoModelForm(request.POST)
            if form.is_valid():
                organization_survey = form.save()
                organization_survey.user = request.user
                organization_survey.save()
                mark_partner_network(organization_survey)
                return redirect(reverse('dashboard'))

    else:
        org_survey_instance = OrganizationSurvey.objects.filter(user=request.user).first()
        if org_survey_instance:
            form = forms.OrganizationInfoModelForm(instance=org_survey_instance)
        else:
            form = forms.OrganizationInfoModelForm()

    context = {'form': form}

    user = request.user
    context.update(get_un_submitted_surveys(user))

    return render(request, 'organization_survey.html', context)


@csrf_exempt
def get_country_names(request):
    """
    Returns country names.
    """
    if request.is_ajax():
        file_path = path(os.path.join(
            'lms', 'djangoapps', 'onboarding_survey', 'data', 'world_countries.json'
        )).abspath()
        with open(file_path) as json_data:
            q = request.GET.get('term', '')
            all_countries = json.load(json_data)
            filtered_countries = [country for country in all_countries if q.lower() in country.lower()]

        data = json.dumps(filtered_countries)

    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)


@csrf_exempt
def get_languages(request):
    """
    Returns languages
    """
    if request.is_ajax():
        file_path = path(os.path.join(
            'lms', 'djangoapps', 'onboarding_survey', 'data', 'world_languages.json'
        )).abspath()
        with open(file_path) as json_data:
            q = request.GET.get('term', '')
            all_languages = json.load(json_data)
            filtered_languages = [language for language in all_languages if q.lower() in language.lower()]

        data = json.dumps(filtered_languages)

    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)
