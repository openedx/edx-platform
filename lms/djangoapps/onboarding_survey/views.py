"""
Views for on-boarding app.
"""
import json
import os
import logging

from path import Path as path

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from lms.djangoapps.onboarding_survey.models import (
    UserInfoSurvey,
    InterestsSurvey,
    OrganizationSurvey,
    Organization)
from lms.djangoapps.onboarding_survey.history import update_history
from onboarding_survey import forms

log = logging.getLogger("edx.onboarding_survey")


def update_user_history(user):
    if user.extended_profile.is_survey_completed:
        update_history(user)


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
    are_forms_complete = request.user.extended_profile.is_survey_completed
    if request.method == 'POST':
        try:
            form = forms.UserInfoModelForm(request.POST, instance=request.user.user_info_survey)
            if form.is_valid():
                form.save()
                update_user_history(request.user)
                if not are_forms_complete:
                    return redirect(reverse('interests'))
                return redirect(reverse('user_info'))

        except UserInfoSurvey.DoesNotExist:
            form = forms.UserInfoModelForm(request.POST)
            if form.is_valid():
                user_info_survey = form.save()
                user_info_survey.user = request.user
                user_info_survey.save()
                update_user_history(request.user)
                if not are_forms_complete:
                    return redirect(reverse('interests'))
                return redirect(reverse('user_info'))

    else:
        user_info_instance = UserInfoSurvey.objects.filter(user=request.user).first()
        if user_info_instance:
            if user_info_instance.dob:
                form = forms.UserInfoModelForm(
                    instance=user_info_instance, initial={'dob': user_info_instance.dob.strftime("%m/%d/%Y")}
                )
            else:
                form = forms.UserInfoModelForm(
                    instance=user_info_instance
                )
        else:
            form = forms.UserInfoModelForm()

    context = {'form': form, 'are_forms_complete': are_forms_complete}
    user = request.user
    context.update(get_un_submitted_surveys(user))
    return render(request, 'onboarding_survey/tell_us_more_survey.html', context)


@login_required
def interests(request):
    """
    The view to handle interests survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to the next survey
    namely, organization survey.
    """
    are_forms_complete = request.user.extended_profile.is_survey_completed
    if request.method == 'POST':
        try:
            form = forms.InterestModelForm(request.POST, instance=request.user.interest_survey)
            if form.is_valid():
                form.save()
                update_user_history(request.user)
                if not are_forms_complete:
                    return redirect(reverse('organization'))

                return redirect(reverse('interests'))

        except InterestsSurvey.DoesNotExist:
            form = forms.InterestModelForm(request.POST)
            if form.is_valid():
                interest_survey = form.save()
                interest_survey.user = request.user
                interest_survey.save()
                update_user_history(request.user)
                if not are_forms_complete:
                    return redirect(reverse('organization'))
                return redirect(reverse('interests'))

    else:
        user_interest_survey_instance = InterestsSurvey.objects.filter(user=request.user).first()
        if user_interest_survey_instance:
            form = forms.InterestModelForm(label_suffix="", instance=user_interest_survey_instance)
        else:
            form = forms.InterestModelForm(label_suffix="")

    context = {'form': form, 'are_forms_complete': are_forms_complete}

    user = request.user
    context.update(get_un_submitted_surveys(user))
    return render(request, 'onboarding_survey/interests_survey.html', context)


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

    def set_survey_complete(extended_profile):
        extended_profile.is_survey_completed = True
        extended_profile.save()
        update_user_history(request.user)

    are_forms_complete = request.user.extended_profile.is_survey_completed
    if request.method == 'POST':

        try:
            form = forms.OrganizationInfoModelForm(request.POST, instance=request.user.organization_survey)
            if form.is_valid():
                organization_survey = form.save()
                update_user_history(request.user)
                mark_partner_network(organization_survey)

                if not are_forms_complete:
                    set_survey_complete(request.user.extended_profile)
                    return redirect(reverse('dashboard'))
                return redirect(reverse('organization'))

        except OrganizationSurvey.DoesNotExist:
            form = forms.OrganizationInfoModelForm(request.POST)
            if form.is_valid():
                organization_survey = form.save()
                update_user_history(request.user)
                organization_survey.user = request.user
                organization_survey.save()
                mark_partner_network(organization_survey)

                if not are_forms_complete:
                    set_survey_complete(request.user.extended_profile)
                    return redirect(reverse('dashboard'))

                return redirect(reverse('organization'))

    else:
        org_survey_instance = OrganizationSurvey.objects.filter(user=request.user).first()
        if org_survey_instance:
            form = forms.OrganizationInfoModelForm(instance=org_survey_instance)
        else:
            form = forms.OrganizationInfoModelForm()

    context = {'form': form, 'are_forms_complete': are_forms_complete}

    user = request.user
    context.update(get_un_submitted_surveys(user))

    return render(request, 'onboarding_survey/organization_survey.html', context)


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


@login_required
def update_account_settings(request):
    """
    View to handle update of registration extra fields
    """
    user_extended_profile = request.user.extended_profile
    if request.method == 'POST':

        form = forms.UpdateRegModelForm(request.POST, instance=user_extended_profile)
        if form.is_valid():
            form_instance = form.save(commit=False)
            if form_instance.is_poc:
                form_instance.org_admin_email = ""
            form_instance.save()
            update_user_history(request.user)

    else:
        form = forms.UpdateRegModelForm(
            instance=user_extended_profile,
            initial={
                'organization_name': user_extended_profile.organization.name,
                'is_poc': 1 if user_extended_profile.is_poc else 0
            }
        )

    return render(
        request, 'onboarding_survey/registration_update.html',
        {'form': form, 'org_url': reverse('get_user_organizations')}
    )


@csrf_exempt
def get_user_organizations(request):
    """
    Get organizations
    """
    final_result = {}
    if request.is_ajax():
        query = request.GET.get('term', '')
        all_organizations = Organization.objects.filter(name__startswith=query)
        for organization in all_organizations:
            final_result[organization.name] = organization.is_poc_exist

        if request.user.is_authenticated():
            user_extended_profile = request.user.extended_profile
            final_result['user_org_info'] = {
                'org': user_extended_profile.organization.name,
                'admin_email': user_extended_profile.org_admin_email
            }

    return JsonResponse(final_result)
