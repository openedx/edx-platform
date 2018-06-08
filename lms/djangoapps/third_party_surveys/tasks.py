from datetime import datetime
from logging import getLogger

import pytz
from django.db import IntegrityError

from common.lib.surveygizmo_client.client import SurveyGizmoClient
from lms.djangoapps.third_party_surveys.models import ThirdPartySurvey

log = getLogger(__name__)


def get_third_party_surveys():
    """
    Periodic Task that will run on daily basis and will sync the response data
    of all surveys thorough Survey Gizmo APIs
    We are scheduling this task through Jenkins instead of celery beat.
    """
    try:
        last_survey = ThirdPartySurvey.objects.latest('request_date')
        filters = [('datesubmitted', '>', last_survey.request_date)]
    except ThirdPartySurvey.DoesNotExist:
        filters = []
    # filters += [('status', '=', 'Completed')]
    survey_responses = SurveyGizmoClient().get_filtered_survey_responses(survey_filters=filters)
    save_responses(survey_responses)


def save_responses(survey_responses):
    surveys_to_create = []

    log.info("survey logs")
    for response in survey_responses:
        log.info(response)
        if response.get('[url("edx_uid")]') \
                or response.get('[url("edx_uid")]') == 'undefined' \
                or response.get('[url("status")]') == 'Deleted':

            continue
        date = datetime.strptime(response['datesubmitted'], "%Y-%m-%d %H:%M:%S")
        try:
            surveys_to_create.append(ThirdPartySurvey(
                response=response,
                user_id=response.get('[url("edx_uid")]'),
                request_date=date,
                survey_type=response.get('[url("app")]', '')
                )
            )
        except (IntegrityError, ValueError) as exc:
            log.info(str(exc))
            log.error(exc)

    # Pass the exception if the user=edx_uid doesn't exist in the Database
    try:
        log.info("bulk insert")
        log.info(surveys_to_create)
        ThirdPartySurvey.objects.bulk_create(surveys_to_create)
    except (IntegrityError, ValueError) as exc:
        log.error(exc)
