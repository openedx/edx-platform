"""Tests for the Tagging models"""
import time

import ddt
from django.test.testcases import TestCase

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import ObjectTag, Tag
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
        api.tag_object(
            object_id="course-v1:OeX+DemoX+Demo_Course",
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.value],
        )
        self.all_orgs_course_tag = api.get_object_tags(
            object_id="course-v1:OeX+DemoX+Demo_Course",
        )[0]
        api.tag_object(
            object_id="block-v1:Ax+DemoX+Demo_Course+type@vertical+block@abcde",
            taxonomy=self.taxonomy_all_orgs,
            tags=[self.tag_all_orgs.value],
        )
        self.all_orgs_block_tag = api.get_object_tags(
            object_id="block-v1:Ax+DemoX+Demo_Course+type@vertical+block@abcde",
        )[0]
        api.tag_object(
            object_id="course-v1:Ax+DemoX+Demo_Course",
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.value],
        )
        self.both_orgs_course_tag = api.get_object_tags(
            object_id="course-v1:Ax+DemoX+Demo_Course",
        )[0]
        api.tag_object(
            object_id="block-v1:OeX+DemoX+Demo_Course+type@video+block@abcde",
            taxonomy=self.taxonomy_both_orgs,
            tags=[self.tag_both_orgs.value],
        )
        self.both_orgs_block_tag = api.get_object_tags(
            object_id="block-v1:OeX+DemoX+Demo_Course+type@video+block@abcde",
        )[0]
        api.tag_object(
            object_id="block-v1:OeX+DemoX+Demo_Course+type@html+block@abcde",
            taxonomy=self.taxonomy_one_org,
            tags=[self.tag_one_org.value],
        )
        self.one_org_block_tag = api.get_object_tags(
            object_id="block-v1:OeX+DemoX+Demo_Course+type@html+block@abcde",
        )[0]
        api.tag_object(
            object_id="course-v1:Ax+DemoX+Demo_Course",
            taxonomy=self.taxonomy_disabled,
            tags=[self.tag_disabled.value],
        )
        self.disabled_course_tag = api.get_object_tags(
            object_id="course-v1:Ax+DemoX+Demo_Course",
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
        org_owner = getattr(self, org_attr).short_name if org_attr else None
        taxonomies = list(
            taxonomy.cast()
            for taxonomy in api.get_taxonomies_for_org(
                org_short_name=org_owner, enabled=enabled
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
                api.get_object_tags(
                    object_id=object_tag.object_id,
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
                api.get_object_tags(
                    object_id=object_tag.object_id,
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


class TestGetAllObjectTagsMixin:
    """
    Set up data to test get_all_object_tags functions
    """

    def setUp(self):
        super().setUp()

        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.taxonomy_1 = api.create_taxonomy(name="Taxonomy 1")
        api.set_taxonomy_orgs(self.taxonomy_1, all_orgs=True)
        Tag.objects.create(
            taxonomy=self.taxonomy_1,
            value="Tag 1.1",
        )
        Tag.objects.create(
            taxonomy=self.taxonomy_1,
            value="Tag 1.2",
        )

        self.taxonomy_2 = api.create_taxonomy(name="Taxonomy 2")
        api.set_taxonomy_orgs(self.taxonomy_2, all_orgs=True)

        Tag.objects.create(
            taxonomy=self.taxonomy_2,
            value="Tag 2.1",
        )
        Tag.objects.create(
            taxonomy=self.taxonomy_2,
            value="Tag 2.2",
        )

        api.tag_object(
            object_id="course-v1:orgA+test_course+test_run",
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1'],
        )
        self.course_tags = api.get_object_tags("course-v1:orgA+test_course+test_run")

        # Tag blocks
        api.tag_object(
            object_id="block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1', 'Tag 1.2'],
        )
        self.sequential_tags1 = api.get_object_tags(
            "block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            taxonomy_id=self.taxonomy_1.id,

        )
        api.tag_object(
            object_id="block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        self.sequential_tags2 = api.get_object_tags(
            "block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            taxonomy_id=self.taxonomy_2.id,
        )
        api.tag_object(
            object_id="block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1",
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.2'],
        )
        self.vertical1_tags = api.get_object_tags(
            "block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1"
        )
        api.tag_object(
            object_id="block-v1:orgA+test_course+test_run+type@html+block@test_html",
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        self.html_tags = api.get_object_tags("block-v1:orgA+test_course+test_run+type@html+block@test_html")

        # Create "deleted" object tags, which will be omitted from the results.
        for object_id in (
            "course-v1:orgA+test_course+test_run",
            "block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            "block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1",
            "block-v1:orgA+test_course+test_run+type@html+block@test_html",
        ):
            ObjectTag.objects.create(
                object_id=str(object_id),
                taxonomy=None,
                tag=None,
                _value="deleted tag",
                _name="deleted taxonomy",
            )

        self.expected_course_objecttags = {
            "course-v1:orgA+test_course+test_run": {
                self.taxonomy_1.id: list(self.course_tags),
            },
            "block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential": {
                self.taxonomy_1.id: list(self.sequential_tags1),
                self.taxonomy_2.id: list(self.sequential_tags2),
            },
            "block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1": {
                self.taxonomy_2.id: list(self.vertical1_tags),
            },
            "block-v1:orgA+test_course+test_run+type@html+block@test_html": {
                self.taxonomy_2.id: list(self.html_tags),
            },
        }

        # Library tags and library contents need a unique block_id that is persisted along test runs
        self.block_suffix = str(round(time.time() * 1000))

        api.tag_object(
            object_id=f"lib:orgA:lib_{self.block_suffix}",
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        self.library_tags = api.get_object_tags(f"lib:orgA:lib_{self.block_suffix}")

        api.tag_object(
            object_id=f"lb:orgA:lib_{self.block_suffix}:problem:problem1_{self.block_suffix}",
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1'],
        )
        self.problem1_tags = api.get_object_tags(
            f"lb:orgA:lib_{self.block_suffix}:problem:problem1_{self.block_suffix}"
        )

        api.tag_object(
            object_id=f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.2'],
        )
        self.library_html_tags1 = api.get_object_tags(
            object_id=f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
            taxonomy_id=self.taxonomy_1.id,
        )

        api.tag_object(
            object_id=f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.2'],
        )
        self.library_html_tags2 = api.get_object_tags(
            object_id=f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
            taxonomy_id=self.taxonomy_2.id,
        )

        # Create "deleted" object tags, which will be omitted from the results.
        for object_id in (
            f"lib:orgA:lib_{self.block_suffix}",
            f"lb:orgA:lib_{self.block_suffix}:problem:problem1_{self.block_suffix}",
            f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
        ):
            ObjectTag.objects.create(
                object_id=object_id,
                taxonomy=None,
                tag=None,
                _value="deleted tag",
                _name="deleted taxonomy",
            )

        self.expected_library_objecttags = {
            f"lib:orgA:lib_{self.block_suffix}": {
                self.taxonomy_2.id: list(self.library_tags),
            },
            f"lb:orgA:lib_{self.block_suffix}:problem:problem1_{self.block_suffix}": {
                self.taxonomy_1.id: list(self.problem1_tags),
            },
            f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}": {
                self.taxonomy_1.id: list(self.library_html_tags1),
                self.taxonomy_2.id: list(self.library_html_tags2),
            },
        }


class TestGetAllObjectTags(TestGetAllObjectTagsMixin, TestCase):
    """
    Test get_all_object_tags api function
    """

    def test_get_course_object_tags(self):
        """
        Test the get_all_object_tags function using a course
        """
        with self.assertNumQueries(1):
            object_tags, taxonomies = api.get_all_object_tags(
                CourseKey.from_string("course-v1:orgA+test_course+test_run")
            )

        assert object_tags == self.expected_course_objecttags
        assert taxonomies == {
            self.taxonomy_1.id: self.taxonomy_1,
            self.taxonomy_2.id: self.taxonomy_2,
        }

    def test_get_library_object_tags(self):
        """
        Test the get_all_object_tags function using a library
        """
        with self.assertNumQueries(1):
            object_tags, taxonomies = api.get_all_object_tags(
                LibraryLocatorV2.from_string(f"lib:orgA:lib_{self.block_suffix}")
            )

        assert object_tags == self.expected_library_objecttags
        assert taxonomies == {
            self.taxonomy_1.id: self.taxonomy_1,
            self.taxonomy_2.id: self.taxonomy_2,
        }
