"""
Tests for the advanced settings
"""

import unittest

import ddt

from cms.djangoapps.models.settings.course_metadata import CourseMetadata

working_cofing_block = {
    "teams_configuration": {
        "value": {
            "max_team_size": 4,
            "topics": [
                {
                    "max_team_size": 5,
                    "name": "Topic 1 Name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_negative_team_size = {
    "teams_configuration": {
        "value": {
            "max_team_size": -1,
            "topics": [
                {
                    "max_team_size": 5,
                    "name": "Topic 1 Name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_negative_local_team_size = {
    "teams_configuration": {
        "value": {
            "max_team_size": 2,
            "topics": [
                {
                    "max_team_size": -4,
                    "name": "Topic 1 Name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_duplicate_id = {
    "teams_configuration": {
        "value": {
            "max_team_size": 2,
            "topics": [
                {
                    "max_team_size": 4,
                    "name": "Topic 1 Name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_1_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_negative_team_size_dupe_id = {
    "teams_configuration": {
        "value": {
            "max_team_size": 2,
            "topics": [
                {
                    "max_team_size": -4,
                    "name": "Topic 1 Name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_missing_name = {
    "teams_configuration": {
        "value": {
            "max_team_size": 2,
            "topics": [
                {
                    "max_team_size": 4,
                    "name": "",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}

cofing_block_extra_attribute = {
    "teams_configuration": {
        "value": {
            "max_team_size": 2,
            "topics": [
                {
                    "max_team_size": 4,
                    "name": "Topic 1 name",
                    "id": "topic_1_id",
                    "description": "Topic 1 desc",
                    "type": "public_managed",
                    "foo": "bar"
                },
                {
                    "id": "topic_2_id",
                    "name": "Topic 2 Name",
                    "description": "Topic 2 desc"
                },
                {
                    "id": "topic_3_id",
                    "name": "Topic 3 Name",
                    "description": "Topic 3 desc"
                },
                {
                    "id": "private_topic_1_id",
                    "type": "private_managed",
                    "description": "Private Topic 1 desc",
                    "name": "Private Topic 1 Name"
                },
                {
                    "id": "private_topic_2_id",
                    "type": "private_managed",
                    "description": "Private Topic 2 desc",
                    "name": "Private Topic 2 Name"
                }
            ]
        }
    }
}


@ddt.ddt
class TeamsConfigurationTests(unittest.TestCase):
    """
    Test class for advanced settings of teams
    """

    @ddt.data(
        (working_cofing_block, 0),
        (cofing_block_negative_team_size, 1),
        (cofing_block_negative_local_team_size, 1),
        (cofing_block_duplicate_id, 1),
        (cofing_block_negative_team_size_dupe_id, 2),
        (cofing_block_missing_name, 1),
        (cofing_block_extra_attribute, 1)
    )
    @ddt.unpack
    def test_team_settings(self, config_block, number_of_errors):
        result = CourseMetadata.validate_team_settings(config_block)
        self.assertEqual(len(result), number_of_errors)
