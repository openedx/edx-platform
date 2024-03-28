"""
Test the objecttag_export_helpers module
"""
from unittest.mock import patch

from openedx.core.djangoapps.content_libraries import api as library_api
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

        self.expected_course_tagged_xblock = TaggedContent(
            display_name="Test Course",
            block_id="course-v1:orgA+test_course+test_run",
            category="course",
            children=[],
            object_tags={
                self.taxonomy_1.id: [tag.value for tag in self.course_tags],
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
                self.taxonomy_1.id: [tag.value for tag in self.sequential_tags1],
                self.taxonomy_2.id: [tag.value for tag in self.sequential_tags2],
            },
        )

        assert self.expected_course_tagged_xblock.children is not None  # type guard
        self.expected_course_tagged_xblock.children.append(tagged_sequential)

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
        assert self.expected_course_tagged_xblock.children is not None  # type guard
        self.expected_course_tagged_xblock.children.append(untagged_sequential)
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
                self.taxonomy_2.id: [tag.value for tag in self.vertical1_tags],
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

        BlockFactory.create(
            parent=vertical2,
            category="html",
            display_name="test html",
        )
        tagged_html = TaggedContent(
            display_name="test html",
            block_id="block-v1:orgA+test_course+test_run+type@html+block@test_html",
            category="html",
            children=[],
            object_tags={
                self.taxonomy_2.id: [tag.value for tag in self.html_tags],
            },
        )
        assert untagged_vertical2.children is not None  # type guard
        untagged_vertical2.children.append(tagged_html)

        self.all_course_object_tags, _ = api.get_all_object_tags(self.course.id)
        self.expected_course_tagged_content_list = [
            (self.expected_course_tagged_xblock, 0),
            (tagged_sequential, 1),
            (tagged_vertical, 2),
            (untagged_vertical2, 2),
            (tagged_html, 3),
            (untagged_sequential, 1),
            (untagged_vertical, 2),
        ]

        # Create a library
        self.library = library_api.create_library(
            self.orgA,
            f"lib_{self.block_suffix}",
            "Test Library",
        )
        self.expected_library_tagged_xblock = TaggedContent(
            display_name="Test Library",
            block_id=f"lib:orgA:lib_{self.block_suffix}",
            category="library",
            children=[],
            object_tags={
                self.taxonomy_2.id: [tag.value for tag in self.library_tags],
            },
        )

        library_api.create_library_block(
            self.library.key,
            "problem",
            f"problem1_{self.block_suffix}",
        )
        tagged_problem = TaggedContent(
            display_name="Blank Problem",
            block_id=f"lb:orgA:lib_{self.block_suffix}:problem:problem1_{self.block_suffix}",
            category="problem",
            children=[],
            object_tags={
                self.taxonomy_1.id: [tag.value for tag in self.problem1_tags],
            },
        )

        library_api.create_library_block(
            self.library.key,
            "problem",
            f"problem2_{self.block_suffix}",
        )
        untagged_problem = TaggedContent(
            display_name="Blank Problem",
            block_id=f"lb:orgA:lib_{self.block_suffix}:problem:problem2_{self.block_suffix}",
            category="problem",
            children=[],
            object_tags={},
        )

        library_api.create_library_block(
            self.library.key,
            "html",
            f"html_{self.block_suffix}",
        )
        tagged_library_html = TaggedContent(
            display_name="Text",
            block_id=f"lb:orgA:lib_{self.block_suffix}:html:html_{self.block_suffix}",
            category="html",
            children=[],
            object_tags={
                self.taxonomy_1.id: [tag.value for tag in self.library_html_tags1],
                self.taxonomy_2.id: [tag.value for tag in self.library_html_tags2],
            },
        )

        assert self.expected_library_tagged_xblock.children is not None  # type guard
        # The children are sorted by add order
        self.expected_library_tagged_xblock.children.append(tagged_problem)
        self.expected_library_tagged_xblock.children.append(untagged_problem)
        self.expected_library_tagged_xblock.children.append(tagged_library_html)

        self.all_library_object_tags, _ = api.get_all_object_tags(self.library.key)
        self.expected_library_tagged_content_list = [
            (self.expected_library_tagged_xblock, 0),
            (tagged_problem, 1),
            (untagged_problem, 1),
            (tagged_library_html, 1),
        ]


class TestContentTagChildrenExport(TaggedCourseMixin):  # type: ignore[misc]
    """
    Test helper functions for exporting tagged content
    """
    def test_build_course_object_tree(self) -> None:
        """
        Test if we can export a course
        """
        with self.assertNumQueries(3):
            tagged_course = build_object_tree_with_objecttags(self.course.id, self.all_course_object_tags)

        assert tagged_course == self.expected_course_tagged_xblock

    def test_build_library_object_tree(self) -> None:
        """
        Test if we can export a library
        """
        with self.assertNumQueries(8):
            tagged_library = build_object_tree_with_objecttags(self.library.key, self.all_library_object_tags)

        assert tagged_library == self.expected_library_tagged_xblock

    def test_course_iterate_with_level(self) -> None:
        """
        Test if we can iterate over the tagged course in the correct order
        """
        tagged_content_list = list(iterate_with_level(self.expected_course_tagged_xblock))
        assert tagged_content_list == self.expected_course_tagged_content_list

    def test_library_iterate_with_level(self) -> None:
        """
        Test if we can iterate over the tagged library in the correct order
        """
        tagged_content_list = list(iterate_with_level(self.expected_library_tagged_xblock))
        assert tagged_content_list == self.expected_library_tagged_content_list
