"""Tests for the Tagging models"""
import ddt
from django.test.testcases import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_tagging.core.tagging.models import Tag
from organizations.models import Organization

from .. import api


class TestTaxonomyMixin:
    """
    Sets up data for testing Content Taxonomies.
    """

    def setUp(self):
        super().setUp()
        self.org1 = Organization.objects.create(name="OpenedX", short_name="OeX")
        self.org2 = Organization.objects.create(name="Axim", short_name="Ax")
        # Taxonomies
        self.taxonomy_disabled = api.create_taxonomy(
            name="Learning Objectives",
            # We will disable this taxonomy below, after we have used it to tag some objects.
            # Note: "disabled" taxonomies are not a supported nor user-exposed feature at the moment, so it's not
            # actually that important to test them.
        )
        api.set_taxonomy_orgs(self.taxonomy_disabled, orgs=[self.org1, self.org2])

        self.taxonomy_all_orgs = api.create_taxonomy(name="Content Types")
        api.set_taxonomy_orgs(self.taxonomy_all_orgs, all_orgs=True)

        self.taxonomy_both_orgs = api.create_taxonomy(name="OpenedX/Axim Content Types")
        api.set_taxonomy_orgs(self.taxonomy_both_orgs, orgs=[self.org1, self.org2])

        self.taxonomy_one_org = api.create_taxonomy(name="OpenedX Content Types")
        api.set_taxonomy_orgs(self.taxonomy_one_org, orgs=[self.org1])

        self.taxonomy_no_orgs = api.create_taxonomy(name="No orgs")

        # Tags
        self.tag_disabled = Tag.objects.create(
            taxonomy=self.taxonomy_disabled,
            value="learning",
        )
        self.tag_all_orgs = Tag.objects.create(
            taxonomy=self.taxonomy_all_orgs,
            value="learning",
        )
        self.tag_both_orgs = Tag.objects.create(
            taxonomy=self.taxonomy_both_orgs,
            value="learning",
        )
        self.tag_one_org = Tag.objects.create(
            taxonomy=self.taxonomy_one_org,
            value="learning",
        )
        self.tag_no_orgs = Tag.objects.create(
            taxonomy=self.taxonomy_no_orgs,
            value="learning",
        )
        # ObjectTags
        self.all_orgs_course_tag = api.tag_content_object(
            object_key=CourseKey.from_string("course-v1:OeX+DemoX+Demo_Course"),
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.value],
        )[0]
        self.all_orgs_block_tag = api.tag_content_object(
            object_key=UsageKey.from_string(
                "block-v1:Ax+DemoX+Demo_Course+type@vertical+block@abcde"
            ),
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.value],
        )[0]
        self.both_orgs_course_tag = api.tag_content_object(
            object_key=CourseKey.from_string("course-v1:Ax+DemoX+Demo_Course"),
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.value],
        )[0]
        self.both_orgs_block_tag = api.tag_content_object(
            object_key=UsageKey.from_string(
                "block-v1:OeX+DemoX+Demo_Course+type@video+block@abcde"
            ),
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.value],
        )[0]
        self.one_org_block_tag = api.tag_content_object(
            object_key=UsageKey.from_string(
                "block-v1:OeX+DemoX+Demo_Course+type@html+block@abcde"
            ),
            taxonomy=self.taxonomy_one_org,
            tags=[self.tag_one_org.value],
        )[0]
        self.disabled_course_tag = api.tag_content_object(
            object_key=CourseKey.from_string("course-v1:Ax+DemoX+Demo_Course"),
            taxonomy=self.taxonomy_disabled,
            tags=[self.tag_disabled.value],
        )[0]
        self.taxonomy_disabled.enabled = False
        self.taxonomy_disabled.save()
        self.disabled_course_tag.refresh_from_db()  # Update its cached .taxonomy


@ddt.ddt
class TestAPITaxonomy(TestTaxonomyMixin, TestCase):
    """
    Tests the Content Taxonomy APIs.
    """

    def test_get_taxonomies_enabled_subclasses(self):
        with self.assertNumQueries(1):
            taxonomies = list(taxonomy.cast() for taxonomy in api.get_taxonomies())
        assert taxonomies == [
            self.taxonomy_all_orgs,
            self.taxonomy_no_orgs,
            self.taxonomy_one_org,
            self.taxonomy_both_orgs,
        ]

    @ddt.data(
        # All orgs
        (None, True, ["taxonomy_all_orgs"]),
        (None, False, []),
        (None, None, ["taxonomy_all_orgs"]),
        # Org 1
        ("org1", True, ["taxonomy_all_orgs", "taxonomy_one_org", "taxonomy_both_orgs"]),
        ("org1", False, ["taxonomy_disabled"]),
        (
            "org1",
            None,
            [
                "taxonomy_all_orgs",
                "taxonomy_disabled",
                "taxonomy_one_org",
                "taxonomy_both_orgs",
            ],
        ),
        # Org 2
        ("org2", True, ["taxonomy_all_orgs", "taxonomy_both_orgs"]),
        ("org2", False, ["taxonomy_disabled"]),
        (
            "org2",
            None,
            ["taxonomy_all_orgs", "taxonomy_disabled", "taxonomy_both_orgs"],
        ),
    )
    @ddt.unpack
    def test_get_taxonomies_for_org(self, org_attr, enabled, expected):
        org_owner = getattr(self, org_attr) if org_attr else None
        taxonomies = list(
            taxonomy.cast()
            for taxonomy in api.get_taxonomies_for_org(
                org_owner=org_owner, enabled=enabled
            )
        )
        assert taxonomies == [
            getattr(self, taxonomy_attr) for taxonomy_attr in expected
        ]

    def test_get_unassigned_taxonomies(self):
        expected = ["taxonomy_no_orgs"]
        taxonomies = list(api.get_unassigned_taxonomies())
        assert taxonomies == [
            getattr(self, taxonomy_attr) for taxonomy_attr in expected
        ]

    @ddt.data(
        ("taxonomy_all_orgs", "all_orgs_course_tag"),
        ("taxonomy_all_orgs", "all_orgs_block_tag"),
        ("taxonomy_both_orgs", "both_orgs_course_tag"),
        ("taxonomy_both_orgs", "both_orgs_block_tag"),
        ("taxonomy_one_org", "one_org_block_tag"),
    )
    @ddt.unpack
    def test_get_content_tags_valid_for_org(
        self,
        taxonomy_attr,
        object_tag_attr,
    ):
        taxonomy_id = getattr(self, taxonomy_attr).id
        object_tag = getattr(self, object_tag_attr)
        with self.assertNumQueries(1):
            valid_tags = list(
                api.get_content_tags(
                    object_key=object_tag.object_key,
                    taxonomy_id=taxonomy_id,
                )
            )
        assert len(valid_tags) == 1
        assert valid_tags[0].id == object_tag.id

    @ddt.data(
        ("taxonomy_all_orgs", "all_orgs_course_tag"),
        ("taxonomy_all_orgs", "all_orgs_block_tag"),
        ("taxonomy_both_orgs", "both_orgs_course_tag"),
        ("taxonomy_both_orgs", "both_orgs_block_tag"),
        ("taxonomy_one_org", "one_org_block_tag"),
    )
    @ddt.unpack
    def test_get_content_tags(
        self,
        taxonomy_attr,
        object_tag_attr,
    ):
        taxonomy_id = getattr(self, taxonomy_attr).id
        object_tag = getattr(self, object_tag_attr)
        with self.assertNumQueries(1):
            valid_tags = list(
                api.get_content_tags(
                    object_key=object_tag.object_key,
                    taxonomy_id=taxonomy_id,
                )
            )
        assert len(valid_tags) == 1
        assert valid_tags[0].id == object_tag.id

    def test_get_tags(self):
        result = list(api.get_tags(self.taxonomy_all_orgs))
        assert len(result) == 1
        assert result[0]["value"] == self.tag_all_orgs.value
        assert result[0]["_id"] == self.tag_all_orgs.id
        assert result[0]["parent_value"] is None
        assert result[0]["depth"] == 0

    def test_cannot_tag_across_orgs(self):
        """
        Ensure that I cannot apply tags from a taxonomy that's linked to another
        org.
        """
        # This taxonomy is only linked to the "OpenedX org", so it can't be used for "Axim" content.
        taxonomy = self.taxonomy_one_org
        tags = [self.tag_one_org.value]
        with self.assertRaises(ValueError) as exc:
            api.tag_content_object(
                object_key=CourseKey.from_string("course-v1:Ax+DemoX+Demo_Course"),
                taxonomy=taxonomy,
                tags=tags,
            )
        assert "The specified Taxonomy is not enabled for the content object's org (Ax)" in str(exc.exception)
        # But this will work fine:
        api.tag_content_object(
            object_key=CourseKey.from_string("course-v1:OeX+DemoX+Demo_Course"),
            taxonomy=taxonomy,
            tags=tags,
        )
        # As will this:
        api.tag_content_object(
            object_key=CourseKey.from_string("course-v1:Ax+DemoX+Demo_Course"),
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.value],
        )
