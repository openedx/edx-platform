import json

from django.db import IntegrityError
from django.test import TestCase

from student.tests.factories import UserFactory
from student.tests.tests import UserSettingsEventTestMixin
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from ..tests.factories import UserPreferenceFactory, UserCourseTagFactory, UserOrgTagFactory
from ..models import UserPreference
from ..preferences.api import set_user_preference


class UserPreferenceModelTest(ModuleStoreTestCase):
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
        self._create_and_assert(user=user, key="testkey0", value="")
        self._create_and_assert(user=user, key="testkey1", value="This is some English text!")
        self._create_and_assert(user=user, key="testkey2", value="{'some': 'json'}")
        self._create_and_assert(
            user=user,
            key="testkey3",
            value="\xe8\xbf\x99\xe6\x98\xaf\xe4\xb8\xad\xe5\x9b\xbd\xe6\x96\x87\xe5\xad\x97'"
        )

    def _create_and_assert(self, user, key, value):
        """Create a new preference and assert the values. """
        preference = UserPreferenceFactory.create(user=user, key=key, value=value)
        self.assertEqual(preference.user, user)
        self.assertEqual(preference.key, key)
        self.assertEqual(preference.value, value)
        return preference

    def test_create_user_course_tags(self):
        """Create user preference tags and confirm properties are set accordingly. """
        user = UserFactory.create()
        course = CourseFactory.create()
        tag = UserCourseTagFactory.create(user=user, course_id=course.id, key="testkey", value="foobar")
        self.assertEquals(tag.user, user)
        self.assertEquals(tag.course_id, course.id)
        self.assertEquals(tag.key, "testkey")
        self.assertEquals(tag.value, "foobar")

    def test_create_user_org_tags(self):
        """Create org specific user tags and confirm all properties are set """
        user = UserFactory.create()
        course = CourseFactory.create()
        tag = UserOrgTagFactory.create(user=user, org=course.id.org, key="testkey", value="foobar")
        self.assertEquals(tag.user, user)
        self.assertEquals(tag.org, course.id.org)
        self.assertEquals(tag.key, "testkey")
        self.assertEquals(tag.value, "foobar")
        self.assertIsNotNone(tag.created)
        self.assertIsNotNone(tag.modified)

        # Modify the tag and save it. Check if the modified timestamp is updated.
        original_modified = tag.modified
        tag.value = "barfoo"
        tag.save()
        self.assertEquals(tag.value, "barfoo")
        self.assertNotEqual(original_modified, tag.modified)

    def test_get_value(self):
        """Verifies the behavior of get_value."""

        user = UserFactory.create()
        key = 'testkey'
        value = 'testvalue'

        # does a round trip
        set_user_preference(user, key, value)
        pref = UserPreference.get_value(user, key)
        self.assertEqual(pref, value)

        # get preference for key that doesn't exist for user
        pref = UserPreference.get_value(user, 'testkey_none')
        self.assertIsNone(pref)


class TestUserPreferenceEvents(UserSettingsEventTestMixin, TestCase):
    """
    Mixin for verifying that user preference events are fired correctly.
    """
    def setUp(self):
        super(TestUserPreferenceEvents, self).setUp()
        self.table = "user_api_userpreference"
        self.user = UserFactory.create()
        self.TEST_KEY = "test key"
        self.TEST_VALUE = "test value"
        self.user_preference = UserPreference.objects.create(user=self.user, key=self.TEST_KEY, value=self.TEST_VALUE)
        self.reset_tracker()

    def test_create_user_preference(self):
        """
        Verify that we emit an event when a user preference is created.
        """
        UserPreference.objects.create(user=self.user, key="new key", value="new value")
        self.assert_user_setting_event_emitted(setting='new key', old=None, new="new value")

    def test_update_user_preference(self):
        """
        Verify that we emit an event when a user preference is updated.
        """
        self.user_preference.value = "new value"
        self.user_preference.save()
        self.assert_user_setting_event_emitted(setting=self.TEST_KEY, old=self.TEST_VALUE, new="new value")

    def test_delete_user_preference(self):
        """
        Verify that we emit an event when a user preference is deleted.
        """
        self.user_preference.delete()
        self.assert_user_setting_event_emitted(setting=self.TEST_KEY, old=self.TEST_VALUE, new=None)

    def test_truncated_user_preference_event(self):
        """
        Verify that we truncate the preference value if it is too long.
        """
        MAX_STRING_LENGTH = 12500
        OVERSIZE_STRING_LENGTH = MAX_STRING_LENGTH + 10
        self.user_preference.value = "z" * OVERSIZE_STRING_LENGTH
        self.user_preference.save()
        self.assert_user_setting_event_emitted(
            setting=self.TEST_KEY, old=self.TEST_VALUE, new="z" * MAX_STRING_LENGTH, truncated=["new"]
        )

        self.user_preference.value = "x" * OVERSIZE_STRING_LENGTH
        self.user_preference.save()
        self.assert_user_setting_event_emitted(
            setting=self.TEST_KEY, old="z" * MAX_STRING_LENGTH, new="x" * MAX_STRING_LENGTH, truncated=["old", "new"]
        )
