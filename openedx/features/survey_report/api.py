"""
Contains the logic to manage survey report model.
"""

from django.conf import settings

from openedx.features.survey_report.models import SurveyReport
from openedx.features.survey_report.queries import (
    get_course_enrollments,
    get_recently_active_users,
    get_generated_certificates,
    get_registered_learners,
    get_unique_courses_offered
)
from .models import SURVEY_REPORT_ERROR, SURVEY_REPORT_GENERATED

MAX_WEEKS_SINCE_LAST_LOGIN: int = 4


def get_report_data() -> dict:
    """ Get data from database to generate a new report."""
    courses_offered = get_unique_courses_offered()
    learners = get_recently_active_users(weeks=MAX_WEEKS_SINCE_LAST_LOGIN)
    registered_learners = get_registered_learners()
    certificates = get_generated_certificates()
    enrollments = get_course_enrollments()
    extra_data = settings.SURVEY_REPORT_EXTRA_DATA

    return {
        "courses_offered": courses_offered,
        "learners": learners,
        "registered_learners": registered_learners,
        "generated_certificates": certificates,
        "enrollments": enrollments,
        "extra_data": extra_data,
    }


def generate_report() -> None:
    """ Generate a report with relevant data."""
    data = {}
    survey_report = SurveyReport(**data)
    survey_report.save()

    try:
        data = get_report_data()
        data["state"] = SURVEY_REPORT_GENERATED
        update_report(survey_report.id, data)
    except (Exception, ) as update_report_error:
        update_report(survey_report.id, {"state": SURVEY_REPORT_ERROR})
        raise Exception(update_report_error) from update_report_error


def update_report(survey_report_id: int, data: dict) -> None:
    SurveyReport.objects.filter(id=survey_report_id).update(**data)
