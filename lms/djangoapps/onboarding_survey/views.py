"""
Views for on-boarding app.
"""
import json
import logging

import os
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from path import Path as path

from edxmako.shortcuts import render_to_response
from lms.djangoapps.onboarding_survey.helpers import is_first_signup_in_org
from lms.djangoapps.onboarding_survey.models import (
    UserInfoSurvey,
    InterestsSurvey,
    OrganizationSurvey,
    Organization,
    OrganizationDetailSurvey,
    Currency)
from lms.djangoapps.onboarding_survey.signals import save_interests
from lms.djangoapps.student_dashboard.views import get_recommended_xmodule_courses, get_recommended_communities
from onboarding_survey import forms
from lms.djangoapps.onboarding_survey.history import update_history

log = logging.getLogger("edx.onboarding_survey")


def update_user_history(user):
    if user.extended_profile.is_survey_completed:
        update_history(user)


def set_survey_complete(extended_profile):
        extended_profile.is_survey_completed = True
        extended_profile.save()
        update_user_history(extended_profile.user)


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

    try:
        user.org_detail_survey
    except Exception:
        un_submitted_surveys['org_detail_survey'] = True

    if un_submitted_surveys.get('user_info') and un_submitted_surveys.get('interests') and\
            un_submitted_surveys.get('organization') and un_submitted_surveys.get('org_detail_survey'):
        un_submitted_surveys['user_info'] = False

    elif un_submitted_surveys.get('interests') and un_submitted_surveys.get('organization')\
            and un_submitted_surveys.get('org_detail_survey'):
        un_submitted_surveys['user_info'] = False
        un_submitted_surveys['interests'] = False

    elif un_submitted_surveys.get('organization') and un_submitted_surveys.get('org_detail_survey'):
        un_submitted_surveys['user_info'] = False
        un_submitted_surveys['interests'] = False
        un_submitted_surveys['organization'] = False
    else:
        un_submitted_surveys['user_info'] = False
        un_submitted_surveys['interests'] = False
        un_submitted_surveys['organization'] = False
        un_submitted_surveys['org_detail_survey'] = False

    return un_submitted_surveys


@login_required
@transaction.atomic
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
        existing_survey = None
        try:
            existing_survey = request.user.user_info_survey
        except UserInfoSurvey.DoesNotExist:
            pass

        if existing_survey:
            form = forms.UserInfoModelForm(request.POST, instance=existing_survey)
        else:
            form = forms.UserInfoModelForm(request.POST)

        if form.is_valid():
            user_info_survey = form.save()

            if not existing_survey:
                user_info_survey.user = request.user
                user_info_survey.save()

            update_user_history(request.user)
            if not are_forms_complete:
                return redirect(reverse('interests'))
            return redirect(reverse('user_info'))

    else:
        user_info_instance = UserInfoSurvey.objects.filter(user=request.user).first()
        if user_info_instance:
            form = forms.UserInfoModelForm(
                instance=user_info_instance
            )
        else:
            form = forms.UserInfoModelForm()

    context = {
        'form': form, 'are_forms_complete': are_forms_complete, 'first_name': request.user.extended_profile.first_name
    }
    user = request.user
    extended_profile = user.extended_profile
    context.update(get_un_submitted_surveys(user))
    context['is_poc'] = extended_profile.is_poc
    context['is_first_user'] = is_first_signup_in_org(extended_profile.organization)
    return render(request, 'onboarding_survey/tell_us_more_survey.html', context)


@login_required
@transaction.atomic
def interests(request):
    """
    The view to handle interests survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to the next survey
    namely, organization survey.
    """
    are_forms_complete = request.user.extended_profile.is_survey_completed
    extended_profile = request.user.extended_profile
    if request.method == 'POST':
        existing_survey = None
        try:
            existing_survey = request.user.interest_survey
        except InterestsSurvey.DoesNotExist:
            pass

        if existing_survey:
            form = forms.InterestModelForm(request.POST, instance=existing_survey)
        else:
            form = forms.InterestModelForm(request.POST)

        if form.is_valid():
            interest_survey = form.save()

            if not existing_survey:
                interest_survey.user = request.user
                interest_survey.save()

            save_interests.send(sender=InterestsSurvey, instance=interest_survey)
            update_user_history(request.user)
            if extended_profile.is_poc or is_first_signup_in_org(
                    request.user.extended_profile.organization):
                return redirect(reverse('organization'))

            if not are_forms_complete:
                set_survey_complete(extended_profile)
                return redirect(reverse('recommendations'))

            return redirect(reverse('interests'))

    else:
        user_interest_survey_instance = InterestsSurvey.objects.filter(user=request.user).first()
        if user_interest_survey_instance:
            form = forms.InterestModelForm(label_suffix="", instance=user_interest_survey_instance)
        else:
            form = forms.InterestModelForm(label_suffix="")

    context = {'form': form, 'are_forms_complete': are_forms_complete}

    user = request.user
    extended_profile = user.extended_profile
    context.update(get_un_submitted_surveys(user))
    context['is_poc'] = extended_profile.is_poc
    context['is_first_user'] = is_first_signup_in_org(extended_profile.organization)
    return render(request, 'onboarding_survey/interests_survey.html', context)


def mark_partner_network(organization_survey):
    """
    Marks partner as affiliated if not already.
    """
    partner_network_manager = organization_survey.partner_network
    if partner_network_manager.exists():
        for partner_network in partner_network_manager.all():
            if not partner_network.is_partner_affiliated:
                partner_network.is_partner_affiliated = True
                partner_network.save()


@login_required
@transaction.atomic
def organization(request):
    """
    The view to handle organization survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to recommendations page.
    """

    are_forms_complete = request.user.extended_profile.is_survey_completed
    if request.method == 'POST':
        existing_survey = None

        try:
            existing_survey = request.user.organization_survey
        except OrganizationSurvey.DoesNotExist:
            pass

        if existing_survey:
            form = forms.OrganizationInfoModelForm(request.POST, instance=request.user.organization_survey)
        else:
            form = forms.OrganizationInfoModelForm(request.POST)

        if form.is_valid():
            organization_survey = form.save()

            if not existing_survey:
                organization_survey.user = request.user
                organization_survey.save()

            mark_partner_network(organization_survey)

            update_user_history(request.user)

            if not are_forms_complete:
                return redirect(reverse('org_detail_survey'))

            return redirect(reverse('organization'))

    else:
        org_survey_instance = OrganizationSurvey.objects.filter(user=request.user).first()
        if org_survey_instance:
            form = forms.OrganizationInfoModelForm(instance=org_survey_instance, initial={
                'is_org_url_exist': '1' if org_survey_instance.is_org_url_exist else '0'
            })
        else:
            form = forms.OrganizationInfoModelForm()

    context = {'form': form, 'are_forms_complete': are_forms_complete}

    user = request.user
    extended_profile = user.extended_profile
    context.update(get_un_submitted_surveys(user))

    context['is_poc'] = extended_profile.is_poc
    context['is_first_user'] = is_first_signup_in_org(extended_profile.organization)
    context['organization_name'] = extended_profile.organization.name

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
            filtered_countries = [country for country in all_countries if country.lower().startswith(q.lower())]

        data = json.dumps(filtered_countries)

    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)


@login_required
@transaction.atomic
def org_detail_survey(request):

    are_forms_complete = request.user.extended_profile.is_survey_completed

    if request.method == 'POST':
        existing_survey = None

        try:
            existing_survey = request.user.org_detail_survey
        except OrganizationDetailSurvey.DoesNotExist:
            pass

        if existing_survey:
            form = forms.OrganizationDetailModelForm(request.POST, instance=request.user.org_detail_survey)
        else:
            form = forms.OrganizationDetailModelForm(request.POST)

        if form.is_valid():
            org_detail = form.save()

            if not existing_survey:
                org_detail.user = request.user
                org_detail.save()

            update_user_history(request.user)
            if not are_forms_complete:
                set_survey_complete(request.user.extended_profile)
                return redirect(reverse('recommendations'))

            return redirect(reverse('org_detail_survey'))

    else:
        org_detail_instance = OrganizationDetailSurvey.objects.filter(user=request.user).first()
        if org_detail_instance:
            form = forms.OrganizationDetailModelForm(instance=org_detail_instance, initial={
                'can_provide_info': '1' if org_detail_instance.can_provide_info else '0',
                'info_accuracy': '1' if org_detail_instance.info_accuracy else '0',
                'currency_input': org_detail_instance.currency.alphabetic_code if org_detail_instance.currency else ""
            })
        else:
            form = forms.OrganizationDetailModelForm()

    context = {'form': form, 'are_forms_complete': are_forms_complete}
    user = request.user
    extended_profile = user.extended_profile
    context.update(get_un_submitted_surveys(user))
    context['is_poc'] = extended_profile.is_poc
    context['is_first_user'] = is_first_signup_in_org(extended_profile.organization)
    context['organization_name'] = extended_profile.organization.name
    return render(request, 'onboarding_survey/organization_detail_survey.html', context)


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
            filtered_languages = [language for language in all_languages if language.lower().startswith(q.lower())]

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
        all_organizations = Organization.objects.filter(name__istartswith=query)
        for organization in all_organizations:
            final_result[organization.name] = True if organization.admin else False

        if request.user.is_authenticated():
            user_extended_profile = request.user.extended_profile
            final_result['user_org_info'] = {
                'org': user_extended_profile.organization.name,
                'admin_email': user_extended_profile.org_admin_email
            }

    return JsonResponse(final_result)


@csrf_exempt
def get_currencies(request):
    currencies = []

    if request.is_ajax():
        term = request.GET.get('term', '')
        currencies = Currency.objects.filter(alphabetic_code__istartswith=term).values_list('alphabetic_code',
                                                                                            flat=True).distinct()
    data = json.dumps(list(currencies))
    return HttpResponse(data, 'application/json')


@login_required
def recommendations(request):
    """
    Display recommended courses and communities based on the survey

    """
    recommended_courses = get_recommended_xmodule_courses(request.user)
    recommended_communities = get_recommended_communities(request.user)
    context = {
        'recommended_courses': recommended_courses,
        'recommended_communities': recommended_communities,
    }

    return render_to_response('onboarding_survey/recommendations.html', context)
