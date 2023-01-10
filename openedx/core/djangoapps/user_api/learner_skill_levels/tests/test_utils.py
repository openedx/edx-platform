""" Unit tests for Learner Skill Levels utilities. """

import ddt
from collections import defaultdict
from unittest import mock

from rest_framework.test import APIClient

from common.djangoapps.student.tests.factories import UserFactory

from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.user_api.learner_skill_levels.utils import (
    calculate_user_skill_score,
    generate_skill_score_mapping,
    get_base_url,
    get_job_holder_usernames,
    get_skills_score,
    get_top_skill_categories_for_job,
    update_category_user_scores_map,
    update_edx_average_score,
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from .testutils import (
    DUMMY_CATEGORIES_RESPONSE,
    DUMMY_CATEGORIES_WITH_SCORES,
    DUMMY_USERNAMES_RESPONSE,
    DUMMY_COURSE_DATA_RESPONSE,
    DUMMY_USER_SCORES_MAP,
)


@ddt.ddt
class LearnerSkillLevelsUtilsTests(SharedModuleStoreTestCase, CatalogIntegrationMixin):
    """
    Test LearnerSkillLevel utilities.
    """
    SERVICE_USERNAME = 'catalog_service_username'

    def setUp(self):
        """
        Unit tests setup.
        """
        super().setUp()

        self.client = APIClient()
        self.service_user = UserFactory(username=self.SERVICE_USERNAME)
        self.catalog_integration = self.create_catalog_integration()

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_course_run_ids')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_course_run_data')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_course_data')
    def test_generate_skill_score_mapping(
        self,
        mock_get_course_data,
        mock_get_course_run_data,
        mock_get_course_run_ids,
    ):
        """
        Test that skill-score mapping is returned in correct format.
        """
        user = UserFactory(username='edX')
        mock_get_course_run_ids.return_value = ['course-v1:AWS+OTP-AWSD12']
        mock_get_course_run_data.return_value = {'course': 'AWS+OTP'}
        mock_get_course_data.return_value = DUMMY_COURSE_DATA_RESPONSE
        result = generate_skill_score_mapping(user)
        expected_response = {"python": 3, "MongoDB": 3, "Data Science": 3}
        assert result == expected_response

    @ddt.data(
        ([], 0.0),
        (
            [
                {"id": 1, "name": "Financial Management", "score": None},
                {"id": 2, "name": "Fintech", "score": None},
            ], 0.0
        ),
        (
            [
                {"id": 1, "name": "Financial Management", "score": None},
                {"id": 2, "name": "Fintech", "score": None},
            ], 0.0
        ),
        (
            [
                {"id": 1, "name": "Financial Management", "score": 3},
                {"id": 2, "name": "Fintech", "score": 2},
            ], 0.8
        ),
    )
    @ddt.unpack
    def test_calculate_user_skill_score(self, skills_with_score, expected):
        """
        Test that skill-score mapping is returned in correct format.
        """

        result = calculate_user_skill_score(skills_with_score)
        assert result == expected

    @ddt.data(
        ([], {"Financial Management": 1, "Fintech": 3}, []),
        (
            [
                {"id": 1, "name": "Financial Management"},
                {"id": 2, "name": "Fintech"},
            ],
            {
                "Financial Management": 1,
                "Fintech": 3
            },
            [
                {"id": 1, "name": "Financial Management", "score": 1},
                {"id": 2, "name": "Fintech", "score": 3},
            ],
        ),
        (
            [
                {"id": 1, "name": "Financial Management"},
                {"id": 2, "name": "Fintech"},
            ],
            {},
            [
                {"id": 1, "name": "Financial Management", "score": None},
                {"id": 2, "name": "Fintech", "score": None},
            ],
        ),
        (
            [
                {"id": 1, "name": "Financial Management"},
                {"id": 2, "name": "Fintech"},
            ],
            {
                "Python": 1,
                "AI": 3
            },
            [
                {"id": 1, "name": "Financial Management", "score": None},
                {"id": 2, "name": "Fintech", "score": None},
            ],
        ),
    )
    @ddt.unpack
    def test_get_skills_score(self, skills, learner_skill_score, expected):
        """
        Test that skill-score mapping is returned in correct format.
        """
        get_skills_score(skills, learner_skill_score)
        assert skills == expected

    def test_update_category_user_scores_map(self):
        """
        Test that skill-score mapping is returned in correct format.
        """
        category_user_scores_map = defaultdict(list)
        update_category_user_scores_map(DUMMY_CATEGORIES_WITH_SCORES["skill_categories"], category_user_scores_map)
        expected = {"Information Technology": [0.8], "Finance": [0.3]}
        assert category_user_scores_map == expected

    def test_update_edx_average_score(self):
        """
        Test that skill-score mapping is returned in correct format.
        """
        update_edx_average_score(DUMMY_CATEGORIES_WITH_SCORES["skill_categories"], DUMMY_USER_SCORES_MAP)
        assert DUMMY_CATEGORIES_WITH_SCORES["skill_categories"][0]["edx_average_score"] == 0.4
        assert DUMMY_CATEGORIES_WITH_SCORES["skill_categories"][1]["edx_average_score"] == 0.5

    @ddt.data(
        ("http://localhost:18000/api/", "http://localhost:18000"),
        ("http://localhost:18000/", "http://localhost:18000"),
    )
    @ddt.unpack
    def test_get_base_url(self, source_url, expected):
        """
        Test that base url is returned correctly.
        """
        actual = get_base_url(source_url)
        assert actual == expected

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_catalog_api_client')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_catalog_api_base_url')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_api_data')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.check_catalog_integration_and_get_user')
    def test_get_top_skill_categories_for_job(
        self,
        mock_check_catalog_integration_and_get_user,
        mock_get_api_data,
        mock_get_catalog_api_base_url,
        mock_get_catalog_api_client
    ):
        """
        Test that get_top_skill_categories_for_job returns jobs categories.
        """
        mock_check_catalog_integration_and_get_user.return_value = self.service_user, self.catalog_integration
        mock_get_api_data.return_value = DUMMY_CATEGORIES_RESPONSE
        mock_get_catalog_api_base_url.return_value = 'localhost:18381/api'
        mock_get_catalog_api_client.return_value = self.client
        result = get_top_skill_categories_for_job(1)
        assert result == DUMMY_CATEGORIES_RESPONSE

    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_catalog_api_client')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_catalog_api_base_url')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.get_api_data')
    @mock.patch('openedx.core.djangoapps.user_api.learner_skill_levels.utils.check_catalog_integration_and_get_user')
    def test_get_job_holder_usernames(
        self,
        mock_check_catalog_integration_and_get_user,
        mock_get_api_data,
        mock_get_catalog_api_base_url,
        mock_get_catalog_api_client
    ):
        """
        Test that test_get_job_holder_usernames returns usernames.
        """
        mock_check_catalog_integration_and_get_user.return_value = self.service_user, self.catalog_integration
        mock_get_api_data.return_value = DUMMY_USERNAMES_RESPONSE
        mock_get_catalog_api_base_url.return_value = 'localhost:18381/api'
        mock_get_catalog_api_client.return_value = self.client
        result = get_job_holder_usernames(1)
        assert result == DUMMY_USERNAMES_RESPONSE
