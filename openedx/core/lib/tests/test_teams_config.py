"""
Tests for Course Teams configuration.
"""
from __future__ import absolute_import, unicode_literals

import ddt
import six
from django.test import TestCase

from ..teams_config import TeamsConfig, TeamsEnabledWithTeamsets, TeamsEnabledWithTopics


@ddt.ddt
class TeamsConfigTests(TestCase):
    """
    Test cases for `TeamsConfig.from_dict` and `TeamsConfig.to_dict`.
    """

    @ddt.data(
        None,
        {},
        {"max_team_size": 5},
        {"teamsets": []},
        {"topics": None, "random_key": 88},
    )
    def test_empty_teams_config_is_disabled(self, data):
        teams_config = TeamsConfig.from_dict(data)
        assert not teams_config.is_enabled

    INPUT_DATA_1 = {
        "max_team_size": 5,
        "topics": [
            {
                "id": "bananas",
                "max_team_size": 10,
                "management": "student",
                "visibility": "private",
            },
            {
                "id": "bokonism",
                "name": "BOKONISM",
                "description": "Busy busy busy",
                "management": "instructor",
                # max_team_size should be ignored because of instructor management.
                "max_team_size": 2,
            },
            {
                # Clusters with duplicate IDs should be dropped.
                "id": "bananas",
                "name": "All about Bananas",
                "description": "Not to be confused with bandanas",
            },

        ],
    }

    OUTPUT_DATA_1 = {
        "max_team_size": 5,
        "topics": [
            {
                "id": "bananas",
                "name": "bananas",
                "description": "",
                "max_team_size": 10,
                "management": "student",
                "visibility": "private",
            },
            {
                "id": "bokonism",
                "name": "BOKONISM",
                "description": "Busy busy busy",
                "max_team_size": None,
                "management": "instructor",
                "visibility": "public",
            },
        ]
    }

    INPUT_DATA_2 = {
        "teamsets": [
            {
                # Cluster should be dropped due to lack of ID.
                "name": "Assignment about existence",
            },
            {
                # Cluster should be dropped due to invalid ID.
                "id": ["not", "a", "string"],
                "name": "Assignment about strings",
            },
            {
                # Cluster should be dropped due to invalid ID.
                "id": "Not a slug.",
                "name": "Assignment about slugs",
            },
            {
                # All fields invalid except ID;
                # Cluster will exist but have all fallbacks.
                "id": "horses",
                "name": {"assignment", "about", "horses"},
                "description": object(),
                "max_team_size": -1000,
                "management": "matrix",
                "visibility": "",
                "extra_key": "Should be ignored",
            },
        ],
    }

    OUTPUT_DATA_2 = {
        "max_team_size": None,
        "teamsets": [
            {
                "id": "horses",
                "name": "horses",
                "description": "",
                "max_team_size": None,
                "management": "student",
                "visibility": "public",
            },
        ],
    }

    @ddt.data(
        (INPUT_DATA_1, TeamsEnabledWithTopics, OUTPUT_DATA_1),
        (INPUT_DATA_2, TeamsEnabledWithTeamsets, OUTPUT_DATA_2),
    )
    @ddt.unpack
    def test_teams_config_round_trip(self, input_data, expected_class, expected_output_data):
        teams_config = TeamsConfig.from_dict(input_data)
        assert isinstance(teams_config, expected_class)
        actual_output_data = teams_config.to_dict()
        self.assertDictEqual(actual_output_data, expected_output_data)

    @ddt.data(
        (
            "not-a-dict",
            "must be a dict",
        ),
        (
            {"topics": [{'id': 'a-topic'}], "teamsets": [{'id': 'a-teamset'}]},
            "Only one of",
        ),
        (
            {"topics": "not-a-list"},
            "topics/teamsets must be list",
        ),
        (
            {"teamsets": {"also-not": "a-list"}},
            "topics/teamsets must be list",
        ),

    )
    @ddt.unpack
    def test_bad_data_gives_value_errors(self, data, error_message_snippet):
        with six.assertRaisesRegex(self, ValueError, error_message_snippet):
            TeamsConfig.from_dict(data)
