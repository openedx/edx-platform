"""
Test cases for LearnerSkillLevelsView.
"""

from unittest import mock

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from common.djangoapps.student.tests.factories import TEST_PASSWORD, UserFactory

from .testutils import DUMMY_CATEGORIES_RESPONSE, DUMMY_USERNAMES_RESPONSE


class LearnerSkillLevelsViewTests(APITestCase):
    """
    The tests for LearnerSkillLevelsView.
    """

    def setUp(self):
        super().setUp()

        self.client = APIClient()
        self.user = UserFactory.create(password=TEST_PASSWORD)
        self.url = reverse('learner_skill_level', kwargs={'job_id': '1'})

        for username in DUMMY_USERNAMES_RESPONSE['usernames']:
            UserFactory(username=username)

    def test_unauthorized_get_endpoint(self):
        """
        Test that endpoint is only accessible to authorized user.
        """
        response = self.client.get(self.url)
        assert response.status_code == 401

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_top_skill_categories_for_job')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_job_holder_usernames')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.api.generate_skill_score_mapping')
    def test_get_endpoint(
        self,
        mock_generate_skill_score_mapping,
        mock_get_job_holder_usernames,
        mock_get_top_skill_categories_for_job
    ):
        """
        Test that response if returned with correct scores appended.
        """
        mock_get_top_skill_categories_for_job.return_value = DUMMY_CATEGORIES_RESPONSE
        mock_get_job_holder_usernames.return_value = DUMMY_USERNAMES_RESPONSE
        mock_generate_skill_score_mapping.return_value = {'Technology Roadmap': 2, 'Python': 3}

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.client.get(self.url)
        assert response.status_code == 200
        # check if the response is mutated and scores are appended for skills
        # for when some skills are learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][0]['user_score'] == 0.8
        assert response.data['skill_categories'][0]['edx_average_score'] == 0.8

        # for when no skill is learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][1]['user_score'] == 0.0
        assert response.data['skill_categories'][1]['edx_average_score'] == 0.0

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_top_skill_categories_for_job')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_job_holder_usernames')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.api.generate_skill_score_mapping')
    def test_get_with_less_than_5_users(
        self,
        mock_generate_skill_score_mapping,
        mock_get_job_holder_usernames,
        mock_get_top_skill_categories_for_job
    ):
        """
        Test that average value is None when users are less than 5.
        """
        mock_get_top_skill_categories_for_job.return_value = DUMMY_CATEGORIES_RESPONSE
        mock_get_job_holder_usernames.return_value = {"usernames": ['user1', 'user2']}
        mock_generate_skill_score_mapping.return_value = {'Technology Roadmap': 2, 'Python': 3}

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.client.get(self.url)
        assert response.status_code == 200
        # check if the response is mutated and scores are appended for skills
        # for when some skills are learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][0]['user_score'] == 0.8
        assert response.data['skill_categories'][0]['edx_average_score'] is None

        # for when no skill is learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][1]['user_score'] == 0.0
        assert response.data['skill_categories'][1]['edx_average_score'] is None

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_top_skill_categories_for_job')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.views.get_job_holder_usernames')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.api.generate_skill_score_mapping')
    def test_get_no_skills_learned(
        self,
        mock_generate_skill_score_mapping,
        mock_get_job_holder_usernames,
        mock_get_top_skill_categories_for_job
    ):
        """
        Test that score is 0.0 when no skills are learned by a user.
        """
        mock_get_top_skill_categories_for_job.return_value = DUMMY_CATEGORIES_RESPONSE
        mock_get_job_holder_usernames.return_value = DUMMY_USERNAMES_RESPONSE
        mock_generate_skill_score_mapping.return_value = {}

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.client.get(self.url)
        assert response.status_code == 200
        # check if the response is mutated and scores are appended for skills
        # for when some skills are learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][0]['user_score'] == 0.0
        assert response.data['skill_categories'][0]['edx_average_score'] == 0.0

        # for when no skill is learned by user in a category, check if user_score and avg score is appended
        assert response.data['skill_categories'][1]['user_score'] == 0.0
        assert response.data['skill_categories'][1]['edx_average_score'] == 0.0
