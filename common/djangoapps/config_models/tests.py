"""
Tests of ConfigurationModel
"""

from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase

from freezegun import freeze_time

from mock import patch
from config_models.models import ConfigurationModel


class ExampleConfig(ConfigurationModel):
    """
    Test model for testing ``ConfigurationModels``.
    """
    cache_timeout = 300

    string_field = models.TextField()
    int_field = models.IntegerField(default=10)


@patch('config_models.models.cache')
class ConfigurationModelTests(TestCase):
    """
    Tests of ConfigurationModel
    """
    def setUp(self):
        self.user = User()
        self.user.save()

    def test_cache_deleted_on_save(self, mock_cache):
        ExampleConfig(changed_by=self.user).save()
        mock_cache.delete.assert_called_with(ExampleConfig.cache_key_name())

    def test_cache_key_name(self, _mock_cache):
        self.assertEquals(ExampleConfig.cache_key_name(), 'configuration/ExampleConfig/current')

    def test_no_config_empty_cache(self, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleConfig.current()
        self.assertEquals(current.int_field, 10)
        self.assertEquals(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), current, 300)

    def test_no_config_full_cache(self, mock_cache):
        current = ExampleConfig.current()
        self.assertEquals(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            first = ExampleConfig(changed_by=self.user)
            first.string_field = 'first'
            first.save()

        second = ExampleConfig(changed_by=self.user)
        second.string_field = 'second'
        second.save()

        self.assertEquals(ExampleConfig.current().string_field, 'second')

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleConfig(changed_by=self.user)
        first.string_field = 'first'
        first.save()

        ExampleConfig.current()

        mock_cache.set.assert_called_with(ExampleConfig.cache_key_name(), first, 300)
