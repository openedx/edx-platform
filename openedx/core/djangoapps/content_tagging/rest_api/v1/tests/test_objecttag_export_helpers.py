"""
Test the objecttag_export_helpers module
"""
from unittest.mock import patch

from openedx_tagging.core.tagging.models import Tag
from organizations.models import Organization

from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase

from .... import api
from ..objecttag_export_helpers import TaggedContent, build_object_tree_with_objecttags, iterate_with_level


class TaggedCourseMixin(ModuleStoreTestCase):
    """
    Mixin with a course structure and taxonomies
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super().setUp()
        # Create user
        self.user = UserFactory.create()
        self.user_id = self.user.id

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

        self.patcher = patch("openedx.core.djangoapps.content_tagging.tasks.modulestore", return_value=self.store)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()

        # Create course
        self.course = self.store.create_course(
            self.orgA.short_name,
            "test_course",
            "test_run",
            self.user_id,
            fields={'display_name': "Test Course"},
        )
        course_tags = api.tag_content_object(
            object_key=self.course.id,
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1'],
        )

        self.expected_tagged_xblock = TaggedContent(
            display_name=self.course.display_name_with_default,
            block_id=str(self.course.id),
            category=self.course.category,
            children=[],
            object_tags={
                self.taxonomy_1.id: list(course_tags),
            },
        )

        # Create XBlocks
        self.sequential = self.store.create_child(self.user_id, self.course.location, "sequential", "test_sequential")
        # Tag blocks
        sequential_tags1 = api.tag_content_object(
            object_key=self.sequential.location,
            taxonomy=self.taxonomy_1,
            tags=['Tag 1.1', 'Tag 1.2'],
        )
        sequential_tags2 = api.tag_content_object(
            object_key=self.sequential.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        xblock = self.store.get_item(self.sequential.location)
        tagged_sequential = TaggedContent(
            display_name=xblock.display_name_with_default,
            block_id=str(xblock.location),
            category=xblock.category,
            children=[],
            object_tags={
                self.taxonomy_1.id: list(sequential_tags1),
                self.taxonomy_2.id: list(sequential_tags2),
            },
        )

        assert self.expected_tagged_xblock.children is not None  # type guard
        self.expected_tagged_xblock.children.append(tagged_sequential)

        vertical = self.store.create_child(self.user_id, self.sequential.location, "vertical", "test_vertical1")
        vertical_tags = api.tag_content_object(
            object_key=vertical.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.2'],
        )
        xblock = self.store.get_item(vertical.location)
        tagged_vertical = TaggedContent(
            display_name=xblock.display_name_with_default,
            block_id=str(xblock.location),
            category=xblock.category,
            children=[],
            object_tags={
                self.taxonomy_2.id: list(vertical_tags),
            },
        )

        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(tagged_vertical)

        vertical2 = self.store.create_child(self.user_id, self.sequential.location, "vertical", "test_vertical2")
        xblock = self.store.get_item(vertical2.location)
        tagged_vertical2 = TaggedContent(
            display_name=xblock.display_name_with_default,
            block_id=str(xblock.location),
            category=xblock.category,
            children=[],
            object_tags={},
        )
        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(tagged_vertical2)

        html = self.store.create_child(self.user_id, vertical2.location, "html", "test_html")
        html_tags = api.tag_content_object(
            object_key=html.location,
            taxonomy=self.taxonomy_2,
            tags=['Tag 2.1'],
        )
        xblock = self.store.get_item(html.location)
        tagged_text = TaggedContent(
            display_name=xblock.display_name_with_default,
            block_id=str(xblock.location),
            category=xblock.category,
            children=[],
            object_tags={
                self.taxonomy_2.id: list(html_tags),
            },
        )

        assert tagged_vertical2.children is not None  # type guard
        tagged_vertical2.children.append(tagged_text)

        self.all_object_tags, _ = api.get_all_object_tags(self.course.id)
        self.expected_tagged_content_list = [
            (self.expected_tagged_xblock, 0),
            (tagged_sequential, 1),
            (tagged_vertical, 2),
            (tagged_vertical2, 2),
            (tagged_text, 3),
        ]


class TestContentTagChildrenExport(TaggedCourseMixin):  # type: ignore[misc]
    """
    Test helper functions for exporting tagged content
    """
    def test_build_object_tree(self) -> None:
        """
        Test if we can export a course
        """
        # 2 from get_course()
        with self.assertNumQueries(2):
            tagged_xblock = build_object_tree_with_objecttags(self.course.id, self.all_object_tags)

        assert tagged_xblock == self.expected_tagged_xblock

    def test_iterate_with_level(self) -> None:
        """
        Test if we can iterate over the tagged content in the correct order
        """
        tagged_content_list = list(iterate_with_level(self.expected_tagged_xblock))
        assert tagged_content_list == self.expected_tagged_content_list
