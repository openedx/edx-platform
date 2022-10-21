"""
Contains the logic to manage survey report model.
"""

from openedx.features.survey_report.queries import get_unique_courses_offered, currently_learners

def generate_report() -> None:
    """ Generate a report with relevant data."""
    courses_offered=get_unique_courses_offered()
    learners=currently_learners()
