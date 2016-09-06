"""
Tests of the populate_model management command and its helper utils.deserialize_json method.
"""

import textwrap
import os.path

from django.utils import timezone
from django.utils.six import BytesIO

from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.db import models

from config_models.management.commands import populate_model
from config_models.models import ConfigurationModel
from config_models.utils import deserialize_json
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


class ExampleDeserializeConfig(ConfigurationModel):
    """
    Test model for testing deserialization of ``ConfigurationModels`` with keyed configuration.
    """
    KEY_FIELDS = ('name',)

    name = models.TextField()
    int_field = models.IntegerField(default=10)

    def __unicode__(self):
        return "ExampleDeserializeConfig(enabled={}, name={}, int_field={})".format(
            self.enabled, self.name, self.int_field
        )


class DeserializeJSONTests(CacheIsolationTestCase):
    """
    Tests of deserializing the JSON representation of ConfigurationModels.
    """
    def setUp(self):
        super(DeserializeJSONTests, self).setUp()
        self.test_username = 'test_worker'
        User.objects.create_user(username=self.test_username)
        self.fixture_path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')

    def test_deserialize_models(self):
        """
        Tests the "happy path", where 2 instances of the test model should be created.
        A valid username is supplied for the operation.
        """
        start_date = timezone.now()
        with open(self.fixture_path) as data:
            entries_created = deserialize_json(data, self.test_username)
            self.assertEquals(2, entries_created)

        self.assertEquals(2, ExampleDeserializeConfig.objects.count())

        betty = ExampleDeserializeConfig.current('betty')
        self.assertTrue(betty.enabled)
        self.assertEquals(5, betty.int_field)
        self.assertGreater(betty.change_date, start_date)
        self.assertEquals(self.test_username, betty.changed_by.username)

        fred = ExampleDeserializeConfig.current('fred')
        self.assertFalse(fred.enabled)
        self.assertEquals(10, fred.int_field)
        self.assertGreater(fred.change_date, start_date)
        self.assertEquals(self.test_username, fred.changed_by.username)

    def test_existing_entries_not_removed(self):
        """
        Any existing configuration model entries are retained
        (though they may be come history)-- deserialize_json is purely additive.
        """
        ExampleDeserializeConfig(name="fred", enabled=True).save()
        ExampleDeserializeConfig(name="barney", int_field=200).save()

        with open(self.fixture_path) as data:
            entries_created = deserialize_json(data, self.test_username)
            self.assertEquals(2, entries_created)

        self.assertEquals(4, ExampleDeserializeConfig.objects.count())
        self.assertEquals(3, len(ExampleDeserializeConfig.objects.current_set()))

        self.assertEquals(5, ExampleDeserializeConfig.current('betty').int_field)
        self.assertEquals(200, ExampleDeserializeConfig.current('barney').int_field)

        # The JSON file changes "enabled" to False for Fred.
        fred = ExampleDeserializeConfig.current('fred')
        self.assertFalse(fred.enabled)

    def test_duplicate_entries_not_made(self):
        """
        If there is no change in an entry (besides changed_by and change_date),
        a new entry is not made.
        """
        with open(self.fixture_path) as data:
            entries_created = deserialize_json(data, self.test_username)
            self.assertEquals(2, entries_created)

        with open(self.fixture_path) as data:
            entries_created = deserialize_json(data, self.test_username)
            self.assertEquals(0, entries_created)

        # Importing twice will still only result in 2 records (second import a no-op).
        self.assertEquals(2, ExampleDeserializeConfig.objects.count())

        # Change Betty.
        betty = ExampleDeserializeConfig.current('betty')
        betty.int_field = -8
        betty.save()

        self.assertEquals(3, ExampleDeserializeConfig.objects.count())
        self.assertEquals(-8, ExampleDeserializeConfig.current('betty').int_field)

        # Now importing will add a new entry for Betty.
        with open(self.fixture_path) as data:
            entries_created = deserialize_json(data, self.test_username)
            self.assertEquals(1, entries_created)

        self.assertEquals(4, ExampleDeserializeConfig.objects.count())
        self.assertEquals(5, ExampleDeserializeConfig.current('betty').int_field)

    def test_bad_username(self):
        """
        Tests the error handling when the specified user does not exist.
        """
        test_json = textwrap.dedent("""
            {
                "model": "config_models.ExampleDeserializeConfig",
                "data": [{"name": "dino"}]
            }
            """)
        with self.assertRaisesRegexp(Exception, "User matching query does not exist"):
            deserialize_json(BytesIO(test_json), "unknown_username")

    def test_invalid_json(self):
        """
        Tests the error handling when there is invalid JSON.
        """
        test_json = textwrap.dedent("""
            {
                "model": "config_models.ExampleDeserializeConfig",
                "data": [{"name": "dino"
            """)
        with self.assertRaisesRegexp(Exception, "JSON parse error"):
            deserialize_json(BytesIO(test_json), self.test_username)

    def test_invalid_model(self):
        """
        Tests the error handling when the configuration model specified does not exist.
        """
        test_json = textwrap.dedent("""
            {
                "model": "xxx.yyy",
                "data":[{"name": "dino"}]
            }
            """)
        with self.assertRaisesRegexp(Exception, "No installed app"):
            deserialize_json(BytesIO(test_json), self.test_username)


class PopulateModelTestCase(CacheIsolationTestCase):
    """
    Tests of populate model management command.
    """
    def setUp(self):
        super(PopulateModelTestCase, self).setUp()
        self.file_path = os.path.join(os.path.dirname(__file__), 'data', 'data.json')
        self.test_username = 'test_management_worker'
        User.objects.create_user(username=self.test_username)

    def test_run_command(self):
        """
        Tests the "happy path", where 2 instances of the test model should be created.
        A valid username is supplied for the operation.
        """
        _run_command(file=self.file_path, username=self.test_username)
        self.assertEquals(2, ExampleDeserializeConfig.objects.count())

        betty = ExampleDeserializeConfig.current('betty')
        self.assertEquals(self.test_username, betty.changed_by.username)

        fred = ExampleDeserializeConfig.current('fred')
        self.assertEquals(self.test_username, fred.changed_by.username)

    def test_no_user_specified(self):
        """
        Tests that a username must be specified.
        """
        with self.assertRaisesRegexp(CommandError, "A valid username must be specified"):
            _run_command(file=self.file_path)

    def test_bad_user_specified(self):
        """
        Tests that a username must be specified.
        """
        with self.assertRaisesRegexp(Exception, "User matching query does not exist"):
            _run_command(file=self.file_path, username="does_not_exist")

    def test_no_file_specified(self):
        """
        Tests the error handling when no JSON file is supplied.
        """
        with self.assertRaisesRegexp(CommandError, "A file containing JSON must be specified"):
            _run_command(username=self.test_username)

    def test_bad_file_specified(self):
        """
        Tests the error handling when the path to the JSON file is incorrect.
        """
        with self.assertRaisesRegexp(CommandError, "File does/not/exist.json does not exist"):
            _run_command(file="does/not/exist.json", username=self.test_username)


def _run_command(*args, **kwargs):
    """Run the management command to deserializer JSON ConfigurationModel data. """
    command = populate_model.Command()
    return command.handle(*args, **kwargs)
