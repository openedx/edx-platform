"""
Tests of ConfigurationModel
"""

import ddt
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from freezegun import freeze_time

from mock import patch, Mock
from config_models.models import ConfigurationModel
from config_models.views import ConfigurationModelCurrentAPIView


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

    def test_always_insert(self, mock_cache):
        config = ExampleConfig(changed_by=self.user, string_field='first')
        config.save()
        config.string_field = 'second'
        config.save()

        self.assertEquals(2, ExampleConfig.objects.all().count())


@ddt.ddt
class ConfigurationModelAPITests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@example.com',
            password='test_pass',
        )
        self.user.is_superuser = True
        self.user.save()

        self.current_view = ConfigurationModelCurrentAPIView.as_view(model=ExampleConfig)

        # Disable caching while testing the API
        patcher = patch('config_models.models.cache', Mock(get=Mock(return_value=None)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_insert(self):
        self.assertEquals("", ExampleConfig.current().string_field)

        request = self.factory.post('/config/ExampleConfig', {"string_field": "string_value"})
        request.user = self.user
        response = self.current_view(request)

        self.assertEquals("string_value", ExampleConfig.current().string_field)
        self.assertEquals(self.user, ExampleConfig.current().changed_by)

    def test_multiple_inserts(self):
        for i in xrange(3):
            self.assertEquals(i, ExampleConfig.objects.all().count())

            request = self.factory.post('/config/ExampleConfig', {"string_field": str(i)})
            request.user = self.user
            response = self.current_view(request)
            self.assertEquals(201, response.status_code)

            self.assertEquals(i+1, ExampleConfig.objects.all().count())
            self.assertEquals(str(i), ExampleConfig.current().string_field)

    def test_get_current(self):
        request = self.factory.get('/config/ExampleConfig')
        request.user = self.user
        response = self.current_view(request)
        self.assertEquals('', response.data['string_field'])
        self.assertEquals(10, response.data['int_field'])
        self.assertEquals(None, response.data['changed_by'])
        self.assertEquals(False, response.data['enabled'])
        self.assertEquals(None, response.data['change_date'])

        ExampleConfig(string_field='string_value', int_field=20).save()

        response = self.current_view(request)
        self.assertEquals('string_value', response.data['string_field'])
        self.assertEquals(20, response.data['int_field'])

    @ddt.data(
        ('get', [], 200),
        ('post', [{'string_field': 'string_value', 'int_field': 10}], 201),
    )
    @ddt.unpack
    def test_permissions(self, method, args, status_code):
        request = getattr(self.factory, method)('/config/ExampleConfig', *args)

        request.user = User.objects.create_user(
            username='no-perms',
            email='no-perms@example.com',
            password='no-perms',
        )
        response = self.current_view(request)
        self.assertEquals(403, response.status_code)

        request.user = self.user
        response = self.current_view(request)
        self.assertEquals(status_code, response.status_code)
