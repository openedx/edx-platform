"""Tests for the Tagging models"""
import ddt
from django.test.testcases import TestCase
from openedx_tagging.core.tagging.models import ObjectTag, Tag
from organizations.models import Organization

from .. import api


class TestContentTaxonomyMixin:
    """
    Sets up data for testing ContentTaxonomies.
    """

    def setUp(self):
        super().setUp()
        self.org1 = Organization.objects.create(name="OpenedX", short_name="OeX")
        self.org2 = Organization.objects.create(name="Axim", short_name="Ax")
        self.taxonomy_disabled = api.create_taxonomy(
            name="Learning Objectives",
            enabled=False,
        )
        self.taxonomy_all_orgs = api.create_taxonomy(
            name="Content Types",
            enabled=True,
        )
        self.taxonomy_both_orgs = api.create_taxonomy(
            name="OpenedX/Axim Content Types",
            enabled=True,
            org_owners=[self.org1, self.org2],
        )
        self.taxonomy_one_org = api.create_taxonomy(
            name="OpenedX Content Types",
            enabled=True,
            org_owners=[self.org1],
        )
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
        self.all_orgs_course_tag = api.tag_object(
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.id],
            object_id="course-v1:OeX+DemoX+Demo_Course",
            object_type="course",
        )[0]
        self.all_orgs_block_tag = api.tag_object(
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.id],
            object_id="block-v1:Ax+DemoX+Demo_Course+type@vertical+block@abcde",
            object_type="section",
        )[0]
        self.both_orgs_course_tag = api.tag_object(
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.id],
            object_id="course-v1:Ax+DemoX+Demo_Course",
            object_type="course",
        )[0]
        self.both_orgs_block_tag = api.tag_object(
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.id],
            object_id="block-v1:OeX+DemoX+Demo_Course+type@vertical+block@abcde",
            object_type="section",
        )[0]
        self.one_org_block_tag = api.tag_object(
            taxonomy=self.taxonomy_one_org,
            tags=[self.tag_one_org.id],
            object_id="block-v1:OeX+DemoX+Demo_Course+type@vertical+block@abcde",
            object_type="section",
        )[0]

        # Invalid object tags must be manually created
        self.disabled_course_tag = ObjectTag.objects.create(
            taxonomy=self.taxonomy_disabled,
            tag=self.tag_disabled,
            object_id="course-v1:Ax+DemoX+Demo_Course",
            object_type="course",
        )
        self.all_orgs_invalid_tag = ObjectTag.objects.create(
            taxonomy=self.taxonomy_all_orgs,
            tag=self.tag_all_orgs,
            object_id="course-v1_OpenedX_DemoX_Demo_Course",
            object_type="course",
        )
        self.one_org_invalid_org_tag = ObjectTag.objects.create(
            taxonomy=self.taxonomy_one_org,
            tag=self.tag_one_org,
            object_id="course-v1:Ax+DemoX+Demo_Course",
            object_type="course",
        )


@ddt.ddt
class TestAPIContentTaxonomy(TestContentTaxonomyMixin, TestCase):
    """
    Tests the ContentTaxonomy APIs.
    """

    def test_content_taxonomy_enabled_for_all_orgs(self):
        with self.assertNumQueries(1):
            taxonomies = list(api.get_taxonomies())
        assert taxonomies == [
            self.taxonomy_all_orgs,
        ]

    def test_content_taxonomy_enabled_for_org1(self):
        with self.assertNumQueries(1):
            taxonomies = list(api.get_taxonomies(self.org1))
        assert taxonomies == [
            self.taxonomy_all_orgs,
            self.taxonomy_one_org,
            self.taxonomy_both_orgs,
        ]

    def test_content_taxonomy_enabled_for_org2(self):
        with self.assertNumQueries(1):
            taxonomies = list(api.get_taxonomies(self.org2))
        assert taxonomies == [
            self.taxonomy_all_orgs,
            self.taxonomy_both_orgs,
        ]

    @ddt.data(
        ("taxonomy_all_orgs", "all_orgs_course_tag", 2),
        ("taxonomy_all_orgs", "all_orgs_block_tag", 2),
        ("taxonomy_both_orgs", "both_orgs_course_tag", 3),
        ("taxonomy_both_orgs", "both_orgs_block_tag", 3),
        ("taxonomy_one_org", "one_org_block_tag", 3),
    )
    @ddt.unpack
    def test_get_object_tags_valid_for_org(
        self, taxonomy_attr, object_tag_attr, num_queries
    ):
        object_tag = getattr(self, object_tag_attr)
        with self.assertNumQueries(num_queries):
            valid_tags = api.get_object_tags(
                getattr(self, taxonomy_attr),
                object_tag.object_id,
                object_tag.object_type,
                valid_only=True,
            )
        assert valid_tags == [object_tag]

    @ddt.data(
        ("taxonomy_disabled", "disabled_course_tag", 1),
        ("taxonomy_all_orgs", "all_orgs_course_tag", 1),
        ("taxonomy_all_orgs", "all_orgs_block_tag", 1),
        ("taxonomy_all_orgs", "all_orgs_invalid_tag", 1),
        ("taxonomy_both_orgs", "both_orgs_course_tag", 1),
        ("taxonomy_both_orgs", "both_orgs_block_tag", 1),
        ("taxonomy_one_org", "one_org_block_tag", 1),
        ("taxonomy_one_org", "one_org_invalid_org_tag", 1),
    )
    @ddt.unpack
    def test_get_object_tags_include_invalid(
        self, taxonomy_attr, object_tag_attr, num_queries
    ):
        object_tag = getattr(self, object_tag_attr)
        with self.assertNumQueries(num_queries):
            valid_tags = api.get_object_tags(
                getattr(self, taxonomy_attr),
                object_tag.object_id,
                object_tag.object_type,
                valid_only=False,
            )
        assert valid_tags == [object_tag]

    def test_get_tags(self):
        assert api.get_tags(self.taxonomy_all_orgs) == [self.tag_all_orgs]

    def test_resync_object_tags(self):
        # Only all_orgs_invalid_tag needs re-syncing, because it wasn't created with api.tag_object
        assert (
            api.resync_object_tags(
                ObjectTag.objects.filter(taxonomy=self.taxonomy_all_orgs)
            )
            == 1
        )
        self.taxonomy_all_orgs.delete()
        for object_tag in [
            self.all_orgs_course_tag,
            self.all_orgs_block_tag,
            self.all_orgs_invalid_tag,
        ]:
            object_tag.refresh_from_db()
            assert object_tag.name == "Content Types"
