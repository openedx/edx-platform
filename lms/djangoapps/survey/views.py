"""
View endpoints for Survey
"""

import logging
import json

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseNotFound
)
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.html import escape

from edxmako.shortcuts import render_to_response
from survey.models import SurveyForm
from microsite_configuration import microsite

log = logging.getLogger("edx.survey")


@login_required
def view_survey(request, survey_name):
    """
    View to render the survey to the end user
    """
    redirect_url = request.GET.get('redirect_url')

    return view_student_survey(request.user, survey_name, redirect_url=redirect_url)


def view_student_survey(user, survey_name, course=None, redirect_url=None, is_required=False, optout_redirect_url=None):
    """
    Shared utility method to render a survey form
    NOTE: This method is shared between the Survey and Courseware Djangoapps
    """

    redirect_url = redirect_url if redirect_url else reverse('dashboard')
    dashboard_redirect_url = reverse('dashboard')
    optout_redirect_url = optout_redirect_url if optout_redirect_url else dashboard_redirect_url

    survey = SurveyForm.get(survey_name, throw_if_not_found=False)
    if not survey:
        return HttpResponseRedirect(redirect_url)

    existing_answers = survey.get_answers(user=user)

    # the result set from get_answers, has an outer key with the user_id
    # just remove that outer key to make the JSON payload simplier
    existing_answers = existing_answers[user.id] if user.id in existing_answers else {}

    context = {
        'existing_data_json': json.dumps(existing_answers),
        'postback_url': reverse('submit_answers', args=[survey_name]),
        'redirect_url': redirect_url,
        'optout_redirect_url': optout_redirect_url,
        'dashboard_redirect_url': dashboard_redirect_url,
        'survey_form': survey.form,
        'is_required': is_required,
        'mail_to_link': microsite.get_value('email_from_address', settings.CONTACT_EMAIL),
        'course': course,
    }

    return render_to_response("survey/survey.html", context)


@require_POST
@login_required
def submit_answers(request, survey_name):
    """
    Form submission post-back endpoint.

    NOTE: We do not have a formal definiation of a Survey Form, it's just some authored html
    form fields (via Django Admin site). Therefore we do not do any validation of the submission server side. It is
    assumed that all validation is done via JavaScript in the survey.html file
    """
    survey = SurveyForm.get(survey_name, throw_if_not_found=False)

    if not survey:
        return HttpResponseNotFound()

    answers = {}
    for key in request.POST.keys():
        # support multi-SELECT form values, by string concatenating them with a comma separator
        array_val = request.POST.getlist(key)
        answers[key] = request.POST[key] if len(array_val) == 0 else ','.join(array_val)

    # the URL we are supposed to redirect to is
    # in a hidden form field
    redirect_url = answers['_redirect_url'] if '_redirect_url' in answers else reverse('dashboard')

    # remove the CSRF token and redirect_url from the post-back dictionary,
    # so that we don't store it in the database as these are hidden form fields
    if 'csrfmiddlewaretoken' in answers:
        del answers['csrfmiddlewaretoken']
    if '_redirect_url' in answers:
        del answers['_redirect_url']

    # scrub the remaining answers to make sure nothing malicious from the user gets stored in
    # our database, e.g. JavaScript
    for answer_key in answers.keys():
        answers[answer_key] = escape(answers[answer_key])

    survey.save_user_answers(request.user, answers)

    response_params = json.dumps({
        # The HTTP end-point for the payment processor.
        "redirect_url": redirect_url,
    })

    return HttpResponse(response_params, content_type="text/json")
