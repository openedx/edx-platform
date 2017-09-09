import json
import os

from path import Path as path

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse

from onboarding_survey import forms


# @login_required
def user_info(request):
    if request.method == 'POST':
        form = forms.UserInfoModelForm(request.POST)
        if form.is_valid():
            user_info_survey = form.save(commit=False)
            user_info_survey.user = request.user
            user_info_survey.save()

            return redirect(reverse('interests'))

    else:
        form = forms.UserInfoModelForm()

    return render(request, 'tell_us_more_survey.html', {'form': form})


# @login_required
def interests(request):

    if request.method == 'POST':
        form = forms.InterestModelForm(request.POST)
        if form.is_valid():
            user_interests_survey = form.save(commit=False)
            user_interests_survey.user = request.user
            user_interests_survey.save()

            return redirect(reverse('organization'))
    else:
        form = forms.InterestModelForm()

    return render(request, 'interests_survey.html', {'form': form})


# @login_required
def organization(request):

    if request.method == 'POST':
        form = forms.OrganizationInfoModelForm(request.POST)
        if form.is_valid():
            organization_survey = form.save(commit=False)
            partner_network = organization_survey.partner_network

            if not partner_network.is_partner_affiliated:
                partner_network.is_partner_affiliated = True
                partner_network.save()

            organization_survey.user = request.user
            organization_survey.save()
            return redirect(reverse('dashboard'))
    else:
        form = forms.OrganizationInfoModelForm()

    return render(request, 'organization_survey.html', {'form': form})


@csrf_exempt
def get_country_names(request):
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


