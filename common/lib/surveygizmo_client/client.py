"""
Client to communicate with Survey Gizmo
"""
from django.conf import settings
from surveygizmo import SurveyGizmo


class SurveyGizmoClient(SurveyGizmo):
    """
    Client for Survey Gizmo
    """

    def __init__(self):
        """
        Instantiates the SurveyGizmo API Client.
        """
        super(SurveyGizmoClient, self).__init__(
            api_version='v4',
            api_token=settings.SURVEY_GIZMO_TOKEN,
            api_token_secret=settings.SURVEY_GIZMO_TOKEN_SECRET,
        )

    def get_surveys(self):
        return self.api.survey.list()  # pylint: disable=no-member

    def get_survey_responses(self, survey_id, survey_filters=None, page_no=1, results_per_page=500):
        """
        Returns filtered surveys of the specific page.
        """
        surveys = self.api.surveyresponse.resultsperpage(results_per_page).page(page_no)  # pylint: disable=no-member

        if survey_filters:
            for survey_filter in survey_filters:
                surveys = surveys.filter(survey_filter[0], survey_filter[1], survey_filter[2])

        return surveys.list(survey_id)

    def get_filtered_survey_responses(self, survey_filters=None):
        """
        Filters survey based on the provided survey filters.
        """
        survey_responses_data = []
        surveys = self.get_surveys()

        for survey in surveys['data']:
            survey_responses = self.get_survey_responses(survey['id'], survey_filters=survey_filters)
            if survey_responses['data']:
                survey_responses_data += survey_responses['data']

            # Pagination
            total_pages = survey_responses['total_pages']

            for page in range(int(survey_responses['page']) + 1, int(total_pages) + 1):
                page_responses = self.get_survey_responses(survey['id'], survey_filters=survey_filters, page_no=page)
                if page_responses['data']:
                    survey_responses_data += page_responses['data']

        return survey_responses_data
