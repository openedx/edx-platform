"""
Test for auto-tagging content
"""
from unittest.mock import patch

import ddt
from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings
from openedx_tagging.core.tagging.models import ObjectTag
from organizations.models import Organization

from openedx.core.lib.tests import attr
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.test_mixed_modulestore import CommonMixedModuleStoreSetup

from ..tasks import delete_xblock_tags, update_course_tags, update_xblock_tags

if not settings.configured:
    settings.configure()

LANGUAGE_TAXONOMY_ID = -1


@ddt.ddt
@attr("mongo")
@override_settings(
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_ALWAYS_EAGER=True,
    BROKER_BACKEND="memory",
)
class TestCourseAutoTagging(CommonMixedModuleStoreSetup):
    """
    Test if the handlers are callend and if they call the right tasks
    """

    def _check_tag(self, object_id, taxonomy, value):
        object_tag = ObjectTag.objects.filter(object_id=object_id, taxonomy=taxonomy).first()
        assert object_tag, "Tag not found"
        assert object_tag.value == value, f"Tag value mismatch {object_tag.value} != {value}"
        return True

    @classmethod
    def setUpClass(cls):
        # Run fixtures to create the system defined tags
        super().setUpClass()
        call_command("loaddata", "--app=oel_tagging", "language_taxonomy.yaml")
        call_command("loaddata", "--app=content_tagging", "system_defined.yaml")

    def setUp(self):
        super().setUp()
        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")

    @ddt.data(
        ModuleStoreEnum.Type.mongo,
        ModuleStoreEnum.Type.split,
    )
    @patch("openedx.features.content_tagging.tasks.modulestore")
    def test_create_course_with_xblock(self, default_ms, mock_modulestore):
        with patch.object(update_course_tags, "delay") as mock_update_course_tags:
            self.initdb(default_ms)
            mock_modulestore.return_value = self.store
            # initdb will create a Course and trigger mock_update_course_tags, so we need to reset it
            mock_update_course_tags.reset_mock()

            # Create course
            course = self.store.create_course(
                self.orgA.short_name, "test_course", "test_run", self.user_id, fields={"language": "pt"}
            )
            course_key_str = str(course.id)
            # Check if task was called
            mock_update_course_tags.assert_called_with(course_key_str)

        # Make the actual call synchronously
        assert update_course_tags(course_key_str)

        # Check if the tags are created in the Course
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

        with patch.object(update_xblock_tags, "delay") as mock_update_xblock_tags:
            # Create XBlock
            sequential = self.store.create_child(self.user_id, course.location, "sequential", "test_sequential")
            vertical = self.store.create_child(self.user_id, sequential.location, "vertical", "test_vertical")

            # publish sequential changes
            self.store.publish(sequential.location, self.user_id)

            usage_key_str = str(vertical.location)
            # Check if task was called
            mock_update_xblock_tags.assert_any_call(usage_key_str)

        # Make the actual call synchronously
        assert update_xblock_tags(usage_key_str)

        # Check if the tags are created in the XBlock
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, "Portuguese")

        # Update course language
        with patch.object(update_course_tags, "delay") as mock_update_course_tags:
            course.language = "en"
            self.store.update_item(course, self.user_id)
            # Check if task was called
            mock_update_course_tags.assert_called_with(course_key_str)

        # Make the actual call synchronously
        assert update_course_tags(course_key_str)

        self.store.publish(sequential.location, self.user_id)
        with patch.object(delete_xblock_tags, "delay") as mock_delete_xblock_tags:
            self.store.delete_item(vertical.location, self.user_id)
            mock_delete_xblock_tags.assert_called_with(usage_key_str)
