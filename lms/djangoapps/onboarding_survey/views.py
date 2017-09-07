import json
import os

from path import Path as path

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django_countries import countries
from django.http import HttpResponse

from onboarding_survey import forms


def tell_us_more(request):

    if request.method == 'POST':
        form = forms.TellUsMoreForm(request.POST)
        from nose.tools import set_trace; set_trace()
        if form.is_valid():
            pass

    else:
        form = forms.TellUsMoreForm()

    return render(request, 'tell_us_more_survey.html', {'form': form})


def interests(request):
    form = forms.InterestForm()
    return render(request, 'interests_survey.html', {'form': form})


def organization(request):
    form = forms.OrganizationInfoForm()
    return render(request, 'organization_survey.html', {'form': form})


@csrf_exempt
def get_country_names(request):
    if request.is_ajax():
        all_counties = dict(countries).values()
        data = json.dumps(all_counties)

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
            filtered_languages = [language for language in all_languages if q in language]

        data = json.dumps(filtered_languages)

    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)


