import pytz
from celery import task
from datetime import datetime, timedelta
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
    filters = []
    try:
        surveys_count = ThirdPartySurvey.objects.count()
        if surveys_count:
            last_survey = ThirdPartySurvey.objects.all().order_by('-request_date')[0]
            edt_survey_time = convert_utc_to_edt(last_survey.request_date)
            filters = [('datesubmitted', '>=', edt_survey_time)]
    except Exception as ex:
        log.exception(ex.args)
    survey_responses = SurveyGizmoClient().get_filtered_survey_responses(survey_filters=filters)
    save_responses(survey_responses)


def convert_utc_to_edt(utc_dt):
    utc_dt = utc_dt + timedelta(seconds=1)
    eastern = pytz.timezone('US/Eastern')
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    loc_dt = utc_dt.astimezone(eastern)
    edt_time = eastern.normalize(loc_dt).strftime(fmt)
    return edt_time


@task()
def get_third_party_surveys_task():
    get_third_party_surveys()


def save_responses(survey_responses):
    for response in survey_responses:

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
            log.error(exc)
