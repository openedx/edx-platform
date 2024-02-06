"""
Test the objecttag_export_helpers module
"""
from unittest.mock import patch

from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

from .... import api
from ....tests.test_api import TestGetAllObjectTagsMixin
from ..objecttag_export_helpers import TaggedContent, build_object_tree_with_objecttags, iterate_with_level


class TaggedCourseMixin(TestGetAllObjectTagsMixin, ModuleStoreTestCase):  # type: ignore[misc]
    """
    Mixin with a course structure and taxonomies
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    CREATE_USER = False

    def setUp(self):
        super().setUp()

        # Patch modulestore
        self.patcher = patch("openedx.core.djangoapps.content_tagging.tasks.modulestore", return_value=self.store)
        self.addCleanup(self.patcher.stop)
        self.patcher.start()

        # Create course
        self.course = CourseFactory.create(
            org=self.orgA.short_name,
            number="test_course",
            run="test_run",
            display_name="Test Course",
        )
        self.expected_tagged_xblock = TaggedContent(
            display_name="Test Course",
            block_id="course-v1:orgA+test_course+test_run",
            category="course",
            children=[],
            object_tags={
                self.taxonomy_1.id: list(self.course_tags),
            },
        )

        # Create XBlocks
        self.sequential = BlockFactory.create(
            parent=self.course,
            category="sequential",
            display_name="test sequential",
        )
        # Tag blocks
        tagged_sequential = TaggedContent(
            display_name="test sequential",
            block_id="block-v1:orgA+test_course+test_run+type@sequential+block@test_sequential",
            category="sequential",
            children=[],
            object_tags={
                self.taxonomy_1.id: list(self.sequential_tags1),
                self.taxonomy_2.id: list(self.sequential_tags2),
            },
        )

        assert self.expected_tagged_xblock.children is not None  # type guard
        self.expected_tagged_xblock.children.append(tagged_sequential)

        # Untagged blocks
        sequential2 = BlockFactory.create(
            parent=self.course,
            category="sequential",
            display_name="untagged sequential",
        )
        untagged_sequential = TaggedContent(
            display_name="untagged sequential",
            block_id="block-v1:orgA+test_course+test_run+type@sequential+block@untagged_sequential",
            category="sequential",
            children=[],
            object_tags={},
        )
        assert self.expected_tagged_xblock.children is not None  # type guard
        self.expected_tagged_xblock.children.append(untagged_sequential)
        BlockFactory.create(
            parent=sequential2,
            category="vertical",
            display_name="untagged vertical",
        )
        untagged_vertical = TaggedContent(
            display_name="untagged vertical",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@untagged_vertical",
            category="vertical",
            children=[],
            object_tags={},
        )
        assert untagged_sequential.children is not None  # type guard
        untagged_sequential.children.append(untagged_vertical)
        # /Untagged blocks

        vertical = BlockFactory.create(
            parent=self.sequential,
            category="vertical",
            display_name="test vertical1",
        )
        tagged_vertical = TaggedContent(
            display_name="test vertical1",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical1",
            category="vertical",
            children=[],
            object_tags={
                self.taxonomy_2.id: list(self.vertical1_tags),
            },
        )
        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(tagged_vertical)

        vertical2 = BlockFactory.create(
            parent=self.sequential,
            category="vertical",
            display_name="test vertical2",
        )
        untagged_vertical2 = TaggedContent(
            display_name="test vertical2",
            block_id="block-v1:orgA+test_course+test_run+type@vertical+block@test_vertical2",
            category="vertical",
            children=[],
            object_tags={},
        )
        assert tagged_sequential.children is not None  # type guard
        tagged_sequential.children.append(untagged_vertical2)

        html = BlockFactory.create(
            parent=vertical2,
            category="html",
            display_name="test html",
        )
        tagged_text = TaggedContent(
            display_name="test html",
            block_id="block-v1:orgA+test_course+test_run+type@html+block@test_html",
            category="html",
            children=[],
            object_tags={
                self.taxonomy_2.id: list(self.html_tags),
            },
        )
        assert untagged_vertical2.children is not None  # type guard
        untagged_vertical2.children.append(tagged_text)

        self.all_object_tags, _ = api.get_all_object_tags(self.course.id)
        self.expected_tagged_content_list = [
            (self.expected_tagged_xblock, 0),
            (tagged_sequential, 1),
            (tagged_vertical, 2),
            (untagged_vertical2, 2),
            (tagged_text, 3),
            (untagged_sequential, 1),
            (untagged_vertical, 2),
        ]


class TestContentTagChildrenExport(TaggedCourseMixin):  # type: ignore[misc]
    """
    Test helper functions for exporting tagged content
    """
    def test_build_object_tree(self) -> None:
        """
        Test if we can export a course
        """
        with self.assertNumQueries(3):
            tagged_xblock = build_object_tree_with_objecttags(self.course.id, self.all_object_tags)

        assert tagged_xblock == self.expected_tagged_xblock

    def test_iterate_with_level(self) -> None:
        """
        Test if we can iterate over the tagged content in the correct order
        """
        tagged_content_list = list(iterate_with_level(self.expected_tagged_xblock))
        assert tagged_content_list == self.expected_tagged_content_list
