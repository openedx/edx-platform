"""
Contains the logic to manage survey report model.
"""

from openedx.features.survey_report.queries import (
    currently_learners,
    genarated_certificates,
    get_unique_courses_offered,
    learners_registered,
    course_enrollments
)


def generate_report() -> None:
    """ Generate a report with relevant data."""
    courses_offered = get_unique_courses_offered()
    learners = currently_learners()
    registered = learners_registered()
    certificates = genarated_certificates()
    enrollments = course_enrollments()
