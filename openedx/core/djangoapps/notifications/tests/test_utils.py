"""
Test cases for the notification utility functions.
"""
import unittest

from openedx.core.djangoapps.notifications.utils import aggregate_notification_configs


class TestAggregateNotificationConfigs(unittest.TestCase):
    """
    Test cases for the aggregate_notification_configs function.
    """

    def test_empty_configs_list_returns_default(self):
        """
        If the configs list is empty, the default config should be returned.
        """
        default_config = [{
            "grading": {
                "enabled": False,
                "non_editable": {},
                "notification_types": {
                    "core": {
                        "web": False,
                        "push": False,
                        "email": False,
                        "email_cadence": "Daily"
                    }
                }
            }
        }]

        result = aggregate_notification_configs(default_config)
        assert result == default_config[0]

    def test_enable_notification_type(self):
        """
        If a config enables a notification type, it should be enabled in the result.
        """

        config_list = [
            {
                "grading": {
                    "enabled": False,
                    "non_editable": {},
                    "notification_types": {
                        "core": {
                            "web": False,
                            "push": False,
                            "email": False,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            },
            {
                "grading": {
                    "enabled": True,
                    "notification_types": {
                        "core": {
                            "web": True,
                            "push": True,
                            "email": True,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            }]

        result = aggregate_notification_configs(config_list)
        assert result["grading"]["enabled"] is True
        assert result["grading"]["notification_types"]["core"]["web"] is True
        assert result["grading"]["notification_types"]["core"]["push"] is True
        assert result["grading"]["notification_types"]["core"]["email"] is True
        # Use default email_cadence
        assert result["grading"]["notification_types"]["core"]["email_cadence"] == "Weekly"

    def test_merge_core_notification_types(self):
        """
        Core notification types should be merged across configs.
        """

        config_list = [
            {
                "discussion": {
                    "enabled": True,
                    "core_notification_types": ["new_comment"],
                    "notification_types": {}
                }
            },
            {
                "discussion": {
                    "core_notification_types": ["new_response", "new_comment"]
                }

            }]

        result = aggregate_notification_configs(config_list)
        assert set(result["discussion"]["core_notification_types"]) == {
            "new_comment", "new_response"
        }

    def test_multiple_configs_aggregate(self):
        """
        Multiple configs should be aggregated together.
        """

        config_list = [
            {
                "updates": {
                    "enabled": False,
                    "notification_types": {
                        "course_updates": {
                            "web": False,
                            "push": False,
                            "email": False,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            },
            {
                "updates": {
                    "enabled": True,
                    "notification_types": {
                        "course_updates": {
                            "web": True,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            },
            {
                "updates": {
                    "notification_types": {
                        "course_updates": {
                            "push": True,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            }
        ]

        result = aggregate_notification_configs(config_list)
        assert result["updates"]["enabled"] is True
        assert result["updates"]["notification_types"]["course_updates"]["web"] is True
        assert result["updates"]["notification_types"]["course_updates"]["push"] is True
        assert result["updates"]["notification_types"]["course_updates"]["email"] is False
        # Use default email_cadence
        assert result["updates"]["notification_types"]["course_updates"]["email_cadence"] == "Weekly"

    def test_ignore_unknown_notification_types(self):
        """
        Unknown notification types should be ignored.
        """
        config_list = [
            {
                "grading": {
                    "enabled": False,
                    "notification_types": {
                        "core": {
                            "web": False,
                            "push": False,
                            "email": False,
                            "email_cadence": "Daily"
                        }
                    }
                }
            },
            {
                "grading": {
                    "notification_types": {
                        "unknown_type": {
                            "web": True,
                            "push": True,
                            "email": True
                        }
                    }
                }
            }]

        result = aggregate_notification_configs(config_list)
        assert "unknown_type" not in result["grading"]["notification_types"]
        assert result["grading"]["notification_types"]["core"]["web"] is False

    def test_ignore_unknown_categories(self):
        """
        Unknown categories should be ignored.
        """

        config_list = [
            {
                "grading": {
                    "enabled": False,
                    "notification_types": {}
                }
            },
            {
                "unknown_category": {
                    "enabled": True,
                    "notification_types": {}
                }
            }]

        result = aggregate_notification_configs(config_list)
        assert "unknown_category" not in result
        assert result["grading"]["enabled"] is False

    def test_preserves_default_structure(self):
        """
        The resulting config should have the same structure as the default config.
        """

        config_list = [
            {
                "discussion": {
                    "enabled": False,
                    "non_editable": {"core": ["web"]},
                    "notification_types": {
                        "core": {
                            "web": False,
                            "push": False,
                            "email": False,
                            "email_cadence": "Weekly"
                        }
                    },
                    "core_notification_types": []
                }
            },
            {
                "discussion": {
                    "enabled": True,
                    "extra_field": "should_not_appear"
                }
            }
        ]

        result = aggregate_notification_configs(config_list)
        assert set(result["discussion"].keys()) == {
            "enabled", "non_editable", "notification_types", "core_notification_types"
        }
        assert "extra_field" not in result["discussion"]

    def test_if_email_cadence_has_diff_set_mix_as_value(self):
        """
        If email_cadence is different in the configs, set it to "Mixed".
        """
        config_list = [
            {
                "grading": {
                    "enabled": False,
                    "notification_types": {
                        "core": {
                            "web": False,
                            "push": False,
                            "email": False,
                            "email_cadence": "Daily"
                        }
                    }
                }
            },
            {
                "grading": {
                    "enabled": True,
                    "notification_types": {
                        "core": {
                            "web": True,
                            "push": True,
                            "email": True,
                            "email_cadence": "Weekly"
                        }
                    }
                }
            },
            {
                "grading": {
                    "notification_types": {
                        "core": {
                            "email_cadence": "Monthly"
                        }
                    }
                }
            }
        ]

        result = aggregate_notification_configs(config_list)
        assert result["grading"]["notification_types"]["core"]["email_cadence"] == "Mixed"
