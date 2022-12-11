"""
Tasks for Survey Report.
"""


import logging

from celery import shared_task
from .api import update_report, get_report_data
from .models import SURVEY_REPORT_GENERATED, SURVEY_REPORT_ERROR

log = logging.getLogger('edx.celery.task')


@shared_task(name='openedx.features.survey_report.tasks.generate_survey_report')
def generate_survey_report(survey_report_id: int):
    """
    Tasks to generate a new survey report with non-sensitive data.
    """
    log.info(
        'Started - generate survey report'
    )

    data = get_report_data()
    try:
        update_report(survey_report_id=survey_report_id, data=data)
        state = SURVEY_REPORT_GENERATED
    except (Exception, ):  # pylint: disable=broad-except
        state = SURVEY_REPORT_ERROR
    data = {"state": state}
    update_report(survey_report_id=survey_report_id, data=data)

    log.info('Done - generate survey report')
