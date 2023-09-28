"""
Specialized exceptions for the Survey Djangoapp
"""


class SurveyFormNotFound(Exception):
    """
    Thrown when a SurveyForm is not found in the database
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class SurveyFormNameAlreadyExists(Exception):
    """
    Thrown when a SurveyForm is created but that name already exists
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
