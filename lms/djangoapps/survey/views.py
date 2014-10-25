"""
View endpoints for Survey
"""

import logging
import json

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseNotFound,
    HttpResponseBadRequest, HttpResponseForbidden, Http404
)
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST

from edxmako.shortcuts import render_to_response
from survey.models import SurveyForm

log = logging.getLogger("edx.survey")


@login_required
def view_survey(request, survey_name):
    """
    View to render the survey to the end user
    """
    survey = SurveyForm.get(survey_name, throw_if_not_found=False)

    if not survey:
        redirect_url = request['redirect_url'] if 'redirect_url' in request else reverse('dashboard')
        HttpResponseRedirect(redirect_url)

    existing_answers = survey.get_answers(user=request.user)

    context = {
        'existing_data_json': json.dumps(existing_answers),
        'postback_url': reverse('submit_answers', args=[survey_name]),
        'survey_form': survey.form,
    }

    return render_to_response("survey/survey.html", context)

@require_POST
@login_required
def submit_answers(request, survey_name):
    """
    Form submission post-back endpoint.

    NOTE: We do not have a formal definiation of a Survey Form, it's just some authored html
    form fields. Therefore we do not do any validation of the submission server side. It is
    assumed to be all done in JavaScript in the survey.html file
    """
    survey = SurveyForm.get(survey_name, throw_if_not_found=False)

    if not survey:
        return HttpResponseNotFound()

    answers = request.POST.dict()

    # remove the CSRF token from the post-back dictionary
    if 'csrfmiddlewaretoken' in answers:
        del answers['csrfmiddlewaretoken']

    survey.save_user_answers(request.user, answers)

    redirect_url = request['redirect_url'] if 'redirect_url' in request else reverse('dashboard')
    response_params = json.dumps({
        # The HTTP end-point for the payment processor.
        "redirect_url": redirect_url,
    })

    return HttpResponse(response_params, content_type="text/json")
