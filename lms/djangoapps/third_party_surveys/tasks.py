from celery import task
from datetime import datetime
from logging import getLogger
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
        last_survey = ThirdPartySurvey.objects.latest('gizmo_survey_id')
        filters = [('id', '>', last_survey.gizmo_survey_id)]
    except ThirdPartySurvey.DoesNotExist:
        filters = []
    # filters += [('status', '=', 'Completed')]
    survey_responses = SurveyGizmoClient().get_filtered_survey_responses(survey_filters=filters)
    save_responses(survey_responses)


@task()
def get_third_party_surveys_task():
    get_third_party_surveys()


def save_responses(survey_responses):

    log.info("survey logs")
    for response in survey_responses:
        log.info(response)
        if response.get('[url("edx_uid")]') in ['', 'undefined', None] \
                or response.get('[url("status")]') == 'Deleted':

            continue
        date = datetime.strptime(response['datesubmitted'], "%Y-%m-%d %H:%M:%S")
        try:
            ThirdPartySurvey.objects.create(
                response=response,
                gizmo_survey_id=response.get('id'),
                user_id=response.get('[url("edx_uid")]'),
                request_date=date,
                survey_type=response.get('[url("app")]', '')
            )

        except (IntegrityError, ValueError) as exc:
            log.info(str(exc))
            log.error(exc)
