"""
Contains the logic to manage survey report model.
"""

from openedx.features.survey_report.queries import (
    get_unique_courses_offered,
    get_currently_learners,
    get_learners_registered,
    get_generated_certificates,
    get_course_enrollments,
)

from openedx.features.survey_report.models import SurveyReport


def generate_report() -> None:
    """ Generate a report with relevant data."""
    courses_offered = get_unique_courses_offered()
    learners = get_currently_learners()
    registered = get_learners_registered()
    certificates = get_generated_certificates()
    enrollments = get_course_enrollments()

    SurveyReport(
        courses_offered=courses_offered,
        learners=learners,
        learners_registered=registered,
        generated_certificates=certificates,
        enrollments=enrollments
    )
