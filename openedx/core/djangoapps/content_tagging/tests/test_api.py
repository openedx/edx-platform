"""Tests for the Tagging models"""
import io
import os
import tempfile
import ddt
from django.test.testcases import TestCase
from fs.osfs import OSFS

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_tagging.core.tagging.models import Tag
from organizations.models import Organization
from ..helpers.test_objecttag_export_helpers import TestGetAllObjectTagsMixin, TaggedCourseMixin

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


class TestExportTags(TaggedCourseMixin):
    """
    Tests for export functions
    """
    def setUp(self):
        super().setUp()
        self.expected_csv = (
            '"Name","Type","ID","1-taxonomy-1","2-taxonomy-2"\r\n'
            '"Test Course","course","course-v1:orgA+test_course+test_run","Tag 1.1",""\r\n'
            '"  test sequential","sequential","block-v1:orgA+test_course+test_run+type@sequential+block@test_'
            'sequential","Tag 1.1, Tag 1.2","Tag 2.1"\r\n'
            '"    test vertical1","vertical","block-v1:orgA+test_course+test_run+type@vertical+block@test_'
            'vertical1","","Tag 2.2"\r\n'
            '"    test vertical2","vertical","block-v1:orgA+test_course+test_run+type@vertical+block@test_'
            'vertical2","",""\r\n'
            '"      test html","html","block-v1:orgA+test_course+test_run+type@html+block@test_html","","Tag 2.1"\r\n'
            '"  untagged sequential","sequential","block-v1:orgA+test_course+test_run+type@sequential+block@untagged_'
            'sequential","",""\r\n'
            '"    untagged vertical","vertical","block-v1:orgA+test_course+test_run+type@vertical+block@untagged_'
            'vertical","",""\r\n'
        )

    def test_generate_csv_rows(self) -> None:
        buffer = io.StringIO()
        list(api.generate_csv_rows(str(self.course.id), buffer))
        buffer.seek(0)
        csv_content = buffer.getvalue()
        assert csv_content == self.expected_csv

    def test_export_tags_in_csv_file(self) -> None:
        file_dir_name = tempfile.mkdtemp()
        file_dir = OSFS(file_dir_name)
        file_name = 'tags.csv'

        api.export_tags_in_csv_file(str(self.course.id), file_dir, file_name)

        file_path = os.path.join(file_dir_name, file_name)

        self.assertTrue(os.path.exists(file_path))

        with open(file_path, 'r') as f:
            content = f.read()

        cleaned_content = content.replace('\r\n', '\n')
        cleaned_expected_csv = self.expected_csv.replace('\r\n', '\n')

        self.assertEqual(cleaned_content, cleaned_expected_csv)
