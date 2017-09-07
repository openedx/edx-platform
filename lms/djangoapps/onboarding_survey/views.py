import json
import os
import datetime

from path import Path as path

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django_countries import countries
from django.http import HttpResponse

from onboarding_survey import forms
from lms.djangoapps.onboarding_survey.models import (
    RoleInsideOrg,
    OrgSector,
    OperationLevel,
    FocusArea,
    TotalEmployee,
    TotalVolunteer,
    PartnerNetwork,
    OrganizationSurvey,
    OrganizationalCapacityArea,
    CommunityTypeInterest,
    InclusionInCommunityChoice,
    PersonalGoal,
    InterestsSurvey,
    EducationLevel,
    EnglishProficiency,
    LearnerSurvey
)


def tell_us_more(request):

    if request.method == 'POST':
        form = forms.TellUsMoreForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            english_proficiency = cleaned_data['english_language_proficiency']
            english_proficiency = dict(form.fields['english_language_proficiency'].choices)[int(english_proficiency)]

            education_level = cleaned_data['level_of_education']
            education_level = dict(form.fields['level_of_education'].choices)[int(education_level)]

            user_info = LearnerSurvey()

            user_info.dob = datetime.datetime.strptime(cleaned_data['birth_date'], "%m/%d/%Y")

            user_info.level_of_education = EducationLevel.objects.filter(level=education_level).first()

            user_info.language = cleaned_data['native_language']
            user_info.english_prof = EnglishProficiency.objects.filter(proficiency=english_proficiency).first()

            user_info.country_of_residence = cleaned_data['country']
            user_info.city_of_residence = cleaned_data['city']

            user_info.is_country_or_city_different = bool(cleaned_data['is_city_or_country_of_employment_diff'])

            user_info.country_of_employment = cleaned_data['country_of_employment']
            user_info.city_of_employment = cleaned_data['city_of_employment']

            user_info.save()

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


