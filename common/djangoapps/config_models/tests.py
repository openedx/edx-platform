# -*- coding: utf-8 -*-
"""
Tests of ConfigurationModel
"""

import ddt
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
        super(ConfigurationModelTests, self).setUp()
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

    def test_active_annotation(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleConfig.objects.create(string_field='first')

        ExampleConfig.objects.create(string_field='second')

        rows = ExampleConfig.objects.with_active_flag().order_by('-change_date')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].string_field, 'second')
        self.assertEqual(rows[0].is_active, True)
        self.assertEqual(rows[1].string_field, 'first')
        self.assertEqual(rows[1].is_active, False)


class ExampleKeyedConfig(ConfigurationModel):
    """
    Test model for testing ``ConfigurationModels`` with keyed configuration.

    Does not inherit from ExampleConfig due to how Django handles model inheritance.
    """
    cache_timeout = 300

    KEY_FIELDS = ('left', 'right')

    left = models.CharField(max_length=30)
    right = models.CharField(max_length=30)

    string_field = models.TextField()
    int_field = models.IntegerField(default=10)


@ddt.ddt
@patch('config_models.models.cache')
class KeyedConfigurationModelTests(TestCase):
    """
    Tests for ``ConfigurationModels`` with keyed configuration.
    """
    def setUp(self):
        super(KeyedConfigurationModelTests, self).setUp()
        self.user = User()
        self.user.save()

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_cache_key_name(self, left, right, _mock_cache):
        self.assertEquals(
            ExampleKeyedConfig.cache_key_name(left, right),
            'configuration/ExampleKeyedConfig/current/{},{}'.format(left, right)
        )

    @ddt.data(
        ((), 'left,right'),
        (('left', 'right'), 'left,right'),
        (('left', ), 'left')
    )
    @ddt.unpack
    def test_key_values_cache_key_name(self, args, expected_key, _mock_cache):
        self.assertEquals(
            ExampleKeyedConfig.key_values_cache_key_name(*args),
            'configuration/ExampleKeyedConfig/key_values/{}'.format(expected_key))

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_empty_cache(self, left, right, mock_cache):
        mock_cache.get.return_value = None

        current = ExampleKeyedConfig.current(left, right)
        self.assertEquals(current.int_field, 10)
        self.assertEquals(current.string_field, '')
        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name(left, right), current, 300)

    @ddt.data(('a', 'b'), ('c', 'd'))
    @ddt.unpack
    def test_no_config_full_cache(self, left, right, mock_cache):
        current = ExampleKeyedConfig.current(left, right)
        self.assertEquals(current, mock_cache.get.return_value)

    def test_config_ordering(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_a',
                right='right_a',
                string_field='first_a',
            ).save()

            ExampleKeyedConfig(
                changed_by=self.user,
                left='left_b',
                right='right_b',
                string_field='first_b',
            ).save()

        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_a',
            right='right_a',
            string_field='second_a',
        ).save()
        ExampleKeyedConfig(
            changed_by=self.user,
            left='left_b',
            right='right_b',
            string_field='second_b',
        ).save()

        self.assertEquals(ExampleKeyedConfig.current('left_a', 'right_a').string_field, 'second_a')
        self.assertEquals(ExampleKeyedConfig.current('left_b', 'right_b').string_field, 'second_b')

    def test_cache_set(self, mock_cache):
        mock_cache.get.return_value = None

        first = ExampleKeyedConfig(
            changed_by=self.user,
            left='left',
            right='right',
            string_field='first',
        )
        first.save()

        ExampleKeyedConfig.current('left', 'right')

        mock_cache.set.assert_called_with(ExampleKeyedConfig.cache_key_name('left', 'right'), first, 300)

    def test_key_values(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', changed_by=self.user).save()

        unique_key_pairs = ExampleKeyedConfig.key_values()
        self.assertEquals(len(unique_key_pairs), 2)
        self.assertEquals(set(unique_key_pairs), set([('left_a', 'right_a'), ('left_b', 'right_b')]))
        unique_left_keys = ExampleKeyedConfig.key_values('left', flat=True)
        self.assertEquals(len(unique_left_keys), 2)
        self.assertEquals(set(unique_left_keys), set(['left_a', 'left_b']))

    def test_key_string_values(self, mock_cache):
        """ Ensure str() vs unicode() doesn't cause duplicate cache entries """
        ExampleKeyedConfig(left='left', right=u'〉☃', enabled=True, int_field=10, changed_by=self.user).save()
        mock_cache.get.return_value = None

        entry = ExampleKeyedConfig.current('left', u'〉☃')
        key = mock_cache.get.call_args[0][0]
        self.assertEqual(entry.int_field, 10)
        mock_cache.get.assert_called_with(key)
        self.assertEqual(mock_cache.set.call_args[0][0], key)

        mock_cache.get.reset_mock()
        entry = ExampleKeyedConfig.current(u'left', u'〉☃')
        self.assertEqual(entry.int_field, 10)
        mock_cache.get.assert_called_with(key)

    def test_current_set(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig(left='left_a', right='right_a', int_field=0, changed_by=self.user).save()
            ExampleKeyedConfig(left='left_b', right='right_b', int_field=0, changed_by=self.user).save()

        ExampleKeyedConfig(left='left_a', right='right_a', int_field=1, changed_by=self.user).save()
        ExampleKeyedConfig(left='left_b', right='right_b', int_field=2, changed_by=self.user).save()

        queryset = ExampleKeyedConfig.objects.current_set()
        self.assertEqual(len(queryset.all()), 2)
        self.assertEqual(
            set(queryset.order_by('int_field').values_list('int_field', flat=True)),
            set([1, 2])
        )

    def test_active_annotation(self, mock_cache):
        mock_cache.get.return_value = None

        with freeze_time('2012-01-01'):
            ExampleKeyedConfig.objects.create(left='left_a', right='right_a', string_field='first')
            ExampleKeyedConfig.objects.create(left='left_b', right='right_b', string_field='first')

        ExampleKeyedConfig.objects.create(left='left_a', right='right_a', string_field='second')

        rows = ExampleKeyedConfig.objects.with_active_flag()
        self.assertEqual(len(rows), 3)
        for row in rows:
            if row.left == 'left_a':
                self.assertEqual(row.is_active, row.string_field == 'second')
            else:
                self.assertEqual(row.left, 'left_b')
                self.assertEqual(row.string_field, 'first')
                self.assertEqual(row.is_active, True)

    def test_key_values_cache(self, mock_cache):
        mock_cache.get.return_value = None
        self.assertEquals(ExampleKeyedConfig.key_values(), [])
        mock_cache.set.assert_called_with(ExampleKeyedConfig.key_values_cache_key_name(), [], 300)

        fake_result = [('a', 'b'), ('c', 'd')]
        mock_cache.get.return_value = fake_result
        self.assertEquals(ExampleKeyedConfig.key_values(), fake_result)
