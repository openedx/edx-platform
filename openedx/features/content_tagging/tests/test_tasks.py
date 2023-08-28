"""
Test for auto-tagging content
"""
from __future__ import annotations

from unittest.mock import patch

import ddt
from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings
from openedx_tagging.core.tagging.models import ObjectTag, Taxonomy
from organizations.models import Organization

from openedx.core.lib.tests import attr
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.test_mixed_modulestore import CommonMixedModuleStoreSetup

from .. import api
from ..models import ContentLanguageTaxonomy, TaxonomyOrg

if not settings.configured:
    settings.configure()

LANGUAGE_TAXONOMY_ID = -1


class TestCourseAutoTagging(CommonMixedModuleStoreSetup):
    """
    Test if the handlers are callend and if they call the right tasks
    """

    def _check_tag(self, object_id: str, taxonomy_id: int, value: str | None):
        """
        Check if the ObjectTag exists for the given object_id and taxonomy_id

        If value is None, check if the ObjectTag does not exists
        """
        object_tag = ObjectTag.objects.filter(object_id=object_id, taxonomy_id=taxonomy_id).first()
        if value is None:
            assert not object_tag, f"Expected no tag for taxonomy_id={taxonomy_id}, but one found with value={value}"
        else:
            assert object_tag, f"Tag for taxonomy_id={taxonomy_id} with value={value} with expected, but none found"
            assert object_tag.value == value, f"Tag value mismatch {object_tag.value} != {value}"

        return True

    @classmethod
    def setUpClass(cls):
        # Run fixtures to create the system defined tags
        super().setUpClass()
        call_command("loaddata", "--app=oel_tagging", "language_taxonomy.yaml")

        # Configure language taxonomy
        language_taxonomy = Taxonomy.objects.get(id=-1)
        language_taxonomy.taxonomy_class = ContentLanguageTaxonomy
        language_taxonomy.save()
        TaxonomyOrg.objects.create(id=-1, taxonomy_id=-1, org=None)

    def setUp(self):
        super().setUp()
        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.initdb(ModuleStoreEnum.Type.split)
        self.patcher = patch("openedx.features.content_tagging.tasks.modulestore", return_value=self.store)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    def test_create_course(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name, "test_course", "test_run", self.user_id, fields={"language": "pt"}
        )

        # Check if the tags are created in the Course
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

    def test_update_course(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name, "test_course", "test_run", self.user_id, fields={"language": "pt"}
        )

        # Simulates user manually changing a tag
        lang_taxonomy = Taxonomy.objects.get(pk=LANGUAGE_TAXONOMY_ID)
        api.tag_content_object(lang_taxonomy, ["Spanish"], course.id)

        # Update course language
        course.language = "en"
        self.store.update_item(course, self.user_id)

        # Does not automatically update the tag
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Spanish")

    def test_create_delete_xblock(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name, "test_course", "test_run", self.user_id, fields={"language": "pt"}
        )

        # Create XBlocks
        sequential = self.store.create_child(self.user_id, course.location, "sequential", "test_sequential")
        vertical = self.store.create_child(self.user_id, sequential.location, "vertical", "test_vertical")

        # Publish sequential changes
        self.store.publish(sequential.location, self.user_id)

        usage_key_str = str(vertical.location)

        # Check if the tags are created in the XBlock
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, "Portuguese")

        # Delete the XBlock
        self.store.delete_item(vertical.location, self.user_id)

        # Check if the tags are deleted
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, None)
