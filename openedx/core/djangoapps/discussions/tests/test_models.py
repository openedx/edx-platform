"""
Perform basic validation of the models
"""
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from ..models import DiscussionsConfiguration


class DiscussionsConfigurationModelTest(TestCase):
    """
    Perform basic validation on the configuration model
    """

    def setUp(self):
        """
        Configure shared test data (configuration, course_key, etc.)
        """
        self.course_key_with_defaults = CourseKey.from_string("course-v1:TestX+Course+Configured")
        self.course_key_without_config = CourseKey.from_string("course-v1:TestX+Course+NoConfig")
        self.course_key_with_values = CourseKey.from_string("course-v1:TestX+Course+Values")
        self.configuration_with_defaults = DiscussionsConfiguration(
            context_key=self.course_key_with_defaults,
        )
        self.configuration_with_defaults.save()
        self.configuration_with_values = DiscussionsConfiguration(
            context_key=self.course_key_with_values,
            enabled=False,
            provider_type='cs_comments_service',
            plugin_configuration={
                'url': 'http://localhost',
            },
        )
        self.configuration_with_values.save()
        pass

    def test_get_nonexistent(self):
        """
        Assert we can not fetch a non-existent record
        """
        with self.assertRaises(DiscussionsConfiguration.DoesNotExist):
            configuration = DiscussionsConfiguration.objects.get(
                context_key=self.course_key_without_config,
            )

    def test_get_with_defaults(self):
        """
        Assert we can lookup a record with default values
        """
        configuration = DiscussionsConfiguration.objects.get(context_key=self.course_key_with_defaults)
        assert configuration is not None
        assert configuration.enabled  # by default
        assert configuration.lti_configuration is None
        assert len(configuration.plugin_configuration.keys()) == 0
        assert not configuration.provider_type

    def test_get_with_values(self):
        """
        Assert we can lookup a record with custom values
        """
        configuration = DiscussionsConfiguration.objects.get(context_key=self.course_key_with_values)
        assert configuration is not None
        assert not configuration.enabled
        assert configuration.lti_configuration is None
        assert configuration.plugin_configuration['url'] == self.configuration_with_values.plugin_configuration['url']
        assert configuration.provider_type == self.configuration_with_values.provider_type

    def test_update_defaults(self):
        """
        Assert we can update an existing record
        """
        configuration = DiscussionsConfiguration.objects.get(context_key=self.course_key_with_defaults)
        configuration.enabled = False
        configuration.plugin_configuration = {
            'url': 'http://localhost',
        }
        configuration.provider_type = 'cs_comments_service'
        configuration.save()
        configuration = DiscussionsConfiguration.objects.get(context_key=self.course_key_with_defaults)
        assert configuration is not None
        assert not configuration.enabled
        assert configuration.lti_configuration is None
        assert configuration.plugin_configuration['url'] == 'http://localhost'
        assert configuration.provider_type == 'cs_comments_service'

    def test_is_enabled_nonexistent(self):
        """
        Assert that discussions are disabled, when no configuration exists
        """
        is_enabled = DiscussionsConfiguration.is_enabled(self.course_key_without_config)
        assert not is_enabled

    def test_is_enabled_default(self):
        """
        Assert that discussions are enabled by default, when a configuration exists
        """
        is_enabled = DiscussionsConfiguration.is_enabled(self.course_key_with_defaults)
        assert is_enabled

    def test_is_enabled_explicit(self):
        """
        Assert that discussions can be explitly disabled
        """
        is_enabled = DiscussionsConfiguration.is_enabled(self.course_key_with_values)
        assert not is_enabled
