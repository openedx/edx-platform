"""
Contains the logic to manage survey report model.
"""

from django.conf import settings

from openedx.features.survey_report.models import SurveyReport
from openedx.features.survey_report.queries import (
    get_course_enrollments,
    get_active_learners_in_the_last_weeks,
    get_generated_certificates,
    get_registered_learners,
    get_unique_courses_offered
)


def generate_report() -> None:
    """ Generate a report with relevant data."""
    courses_offered = get_unique_courses_offered()
    learners = get_active_learners_in_the_last_weeks(weeks=3)
    registered = get_registered_learners()
    certificates = get_generated_certificates()
    enrollments = get_course_enrollments()
    extra_data = settings.SURVEY_REPORT_EXTRA_DATA

    survey_report = SurveyReport(
        courses_offered=courses_offered,
        learners=learners,
        registered_learners=registered,
        generated_certificates=certificates,
        enrollments=enrollments,
        extra_data=extra_data,
    )

    survey_report.save()
