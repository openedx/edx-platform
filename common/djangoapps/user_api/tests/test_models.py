from django.db import IntegrityError
from django.test import TestCase
from student.tests.factories import UserFactory
from user_api.tests.factories import UserPreferenceFactory
from user_api.models import UserPreference


class UserPreferenceModelTest(TestCase):
    def test_duplicate_user_key(self):
        user = UserFactory.create()
        UserPreferenceFactory.create(user=user, key="testkey", value="first")
        self.assertRaises(
            IntegrityError,
            UserPreferenceFactory.create,
            user=user,
            key="testkey",
            value="second"
        )

    def test_arbitrary_values(self):
        user = UserFactory.create()
        UserPreferenceFactory.create(user=user, key="testkey0", value="")
        UserPreferenceFactory.create(user=user, key="testkey1", value="This is some English text!")
        UserPreferenceFactory.create(user=user, key="testkey2", value="{'some': 'json'}")
        UserPreferenceFactory.create(
            user=user,
            key="testkey3",
            value="\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\xad\xe5\x9b\xbd\xe6\x96\x87\xe5\xad\x97'"
        )

    def test_get_set_preference(self):
        # tests for the getters and setters of preferences

        user = UserFactory.create()
        key = 'testkey'
        value = 'testvalue'

        # does a round trip
        UserPreference.set_preference(user, key, value)
        pref = UserPreference.get_preference(user, key)

        self.assertEqual(pref, value)

        # get preference for key that doesn't exist for user
        pref = UserPreference.get_preference(user, 'testkey_none')
        self.assertIsNone(pref)
