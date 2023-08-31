"""
Test for auto-tagging content
"""
from __future__ import annotations

from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx_tagging.core.tagging.models import ObjectTag, Tag, Taxonomy
from organizations.models import Organization

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_MODULESTORE, ModuleStoreTestCase

from .. import api
from ..models import ContentLanguageTaxonomy, TaxonomyOrg
from ..toggles import CONTENT_TAGGING_AUTO

LANGUAGE_TAXONOMY_ID = -1


@skip_unless_cms  # Auto-tagging is only available in the CMS
@override_waffle_flag(CONTENT_TAGGING_AUTO, active=True)
class TestAutoTagging(ModuleStoreTestCase):
    """
    Test if the Course and XBlock tags are automatically created
    """

    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def _check_tag(self, object_id: str, taxonomy_id: int, value: str | None):
        """
        Check if the ObjectTag exists for the given object_id and taxonomy_id

        If value is None, check if the ObjectTag does not exists
        """
        object_tag = ObjectTag.objects.filter(object_id=object_id, taxonomy_id=taxonomy_id).first()
        if value is None:
            assert not object_tag, f"Expected no tag for taxonomy_id={taxonomy_id}, " \
                f"but one found with value={object_tag.value}"
        else:
            assert object_tag, f"Tag for taxonomy_id={taxonomy_id} with value={value} with expected, but none found"
            assert object_tag.value == value, f"Tag value mismatch {object_tag.value} != {value}"

        return True

    @classmethod
    def setUpClass(cls):
        # Run fixtures to create the system defined tags
        call_command("loaddata", "--app=oel_tagging", "language_taxonomy.yaml")

        # Configure language taxonomy
        language_taxonomy = Taxonomy.objects.get(id=-1)
        language_taxonomy.taxonomy_class = ContentLanguageTaxonomy
        language_taxonomy.save()

        # Enable Language taxonomy for all orgs
        TaxonomyOrg.objects.create(id=-1, taxonomy=language_taxonomy, org=None)

        super().setUpClass()

    def setUp(self):
        super().setUp()
        # Create user
        self.user = UserFactory.create()
        self.user_id = self.user.id

        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.patcher = patch("openedx.features.content_tagging.tasks.modulestore", return_value=self.store)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()

    def test_create_course(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "pt"},
        )

        # Check if the tags are created in the Course
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

    @override_settings(LANGUAGE_CODE='pt')
    def test_create_course_invalid_language(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "11"},
        )

        # Check if the tags are created in the Course is the system default
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

    @override_settings(LANGUAGES=[('pt', 'Portuguese')], LANGUAGE_CODE='pt')
    def test_create_course_unsuported_language(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "en"},
        )

        # Check if the tags are created in the Course is the system default
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

    @override_settings(LANGUAGE_CODE='pt')
    def test_create_course_no_tag_language(self):
        # Remove English tag
        Tag.objects.filter(taxonomy_id=LANGUAGE_TAXONOMY_ID, value="English").delete()
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "en"},
        )

        # Check if the tags are created in the Course is the system default
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, "Portuguese")

    @override_settings(LANGUAGE_CODE='pt')
    def test_create_course_no_tag_default_language(self):
        # Remove Portuguese tag
        Tag.objects.filter(taxonomy_id=LANGUAGE_TAXONOMY_ID, value="Portuguese").delete()
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "11"},
        )

        # No tags created
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, None)

    def test_update_course(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "pt"},
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
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "pt"},
        )

        # Create XBlocks
        sequential = self.store.create_child(self.user_id, course.location, "sequential", "test_sequential")
        vertical = self.store.create_child(self.user_id, sequential.location, "vertical", "test_vertical")

        usage_key_str = str(vertical.location)

        # Check if the tags are created in the XBlock
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, "Portuguese")

        # Delete the XBlock
        self.store.delete_item(vertical.location, self.user_id)

        # Check if the tags are deleted
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, None)

    @override_waffle_flag(CONTENT_TAGGING_AUTO, active=False)
    def test_waffle_disabled_create_update_course(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "pt"},
        )

        # No tags created
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, None)

        # Update course language
        course.language = "en"
        self.store.update_item(course, self.user_id)

        # No tags created
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, None)

    @override_waffle_flag(CONTENT_TAGGING_AUTO, active=False)
    def test_waffle_disabled_create_delete_xblock(self):
        # Create course
        course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={"language": "pt"},
        )

        # Create XBlocks
        sequential = self.store.create_child(self.user_id, course.location, "sequential", "test_sequential")
        vertical = self.store.create_child(self.user_id, sequential.location, "vertical", "test_vertical")

        usage_key_str = str(vertical.location)

        # No tags created
        assert self._check_tag(course.id, LANGUAGE_TAXONOMY_ID, None)

        # Delete the XBlock
        self.store.delete_item(vertical.location, self.user_id)

        # Still no tags
        assert self._check_tag(usage_key_str, LANGUAGE_TAXONOMY_ID, None)
